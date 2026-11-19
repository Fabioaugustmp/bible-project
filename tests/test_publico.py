"""Publicação atrás do túnel da Cloudflare (D034): código de acesso em todo pedido e origem https."""
import http.client
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import server  # noqa: E402
import userdata  # noqa: E402

HOST = "biblia.famptech.com.br"
ORIGIN = f"https://{HOST}"
SECRET = "codigo-de-teste-com-16-ou-mais"


class Origem(unittest.TestCase):
    def setUp(self):
        self.saved = (userdata.ALLOWED_HOSTS, userdata.PUBLIC_ORIGINS)
        userdata.ALLOWED_HOSTS = {"localhost:8377", HOST}
        userdata.PUBLIC_ORIGINS = {ORIGIN}

    def tearDown(self):
        userdata.ALLOWED_HOSTS, userdata.PUBLIC_ORIGINS = self.saved

    def test_https_do_host_publico_e_aceito(self):
        self.assertTrue(userdata.check_origin({"Host": HOST, "Origin": ORIGIN}))

    def test_http_do_host_publico_e_recusado(self):
        self.assertFalse(userdata.check_origin({"Host": HOST, "Origin": f"http://{HOST}"}))

    def test_origem_de_outro_site_e_recusada(self):
        self.assertFalse(userdata.check_origin({"Host": HOST, "Origin": "https://evil.example"}))
        self.assertFalse(userdata.check_origin({"Host": "evil.example", "Origin": "https://evil.example"}))

    def test_local_continua_como_antes(self):
        self.assertTrue(userdata.check_origin({"Host": "localhost:8377", "Origin": "http://localhost:8377"}))
        self.assertFalse(userdata.check_origin({"Host": "localhost:8377", "Origin": ORIGIN}))


class Codigo(unittest.TestCase):
    """Servidor real em porta livre; sem base, porque os pedidos testados são recusados ou leem só app/static."""

    def setUp(self):
        self.saved = (server.LAN, server.PUBLIC, server.TOKEN, server.PUBLIC_ORIGIN)
        server.LAN, server.PUBLIC, server.TOKEN = False, True, SECRET
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        server.LAN, server.PUBLIC, server.TOKEN, server.PUBLIC_ORIGIN = self.saved

    def get(self, path, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path, headers=headers or {})
        resp = conn.getresponse()
        body = resp.read()
        result = (resp.status, dict(resp.getheaders()), body)
        conn.close()
        return result

    def test_sem_codigo_nao_entra(self):
        status, _, _ = self.get("/index.html")
        self.assertEqual(status, 403)

    def test_codigo_errado_nao_entra(self):
        status, _, _ = self.get("/index.html?t=outro-codigo")
        self.assertEqual(status, 403)
        status, _, _ = self.get("/index.html", {"Cookie": "bp_t=outro-codigo"})
        self.assertEqual(status, 403)

    def test_codigo_na_url_grava_cookie_seguro(self):
        status, headers, _ = self.get(f"/?t={SECRET}")
        self.assertEqual(status, 302)
        cookie = headers.get("Set-Cookie", "")
        self.assertIn(f"bp_t={SECRET}", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)

    def test_cookie_valido_libera_a_interface(self):
        status, _, body = self.get("/index.html", {"Cookie": f"outro=1; bp_t={SECRET}"})
        self.assertEqual(status, 200)
        self.assertIn(b"<", body)

    def test_api_tambem_exige_codigo(self):
        status, _, _ = self.get("/api/library")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
