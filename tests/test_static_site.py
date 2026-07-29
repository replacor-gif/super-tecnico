from __future__ import annotations

import json
import re
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_static import build  # noqa: E402
from audit_brand_quality import audit_brand  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(value: str) -> str:
    value = "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    ).upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", value)).strip()


def contains_query(entries: list[dict], query: str) -> bool:
    tokens = normalized(query).split()
    for item in entries:
        haystack = str(item.get("haystack", ""))
        compact = haystack.replace(" ", "")
        if all(token in haystack or token in compact for token in tokens):
            return True
    return False


class StaticSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.dist = Path(cls.temp.name) / "dist"
        cls.report = build(ROOT, cls.dist)
        cls.brand = cls.dist / "data" / "brands" / "fujitsu-general"
        cls.web = cls.brand / "web"
        cls.daikin = cls.dist / "data" / "brands" / "daikin"
        cls.daikin_web = cls.daikin / "web"
        cls.mitsubishi = cls.dist / "data" / "brands" / "mitsubishi-electric"
        cls.mitsubishi_web = cls.mitsubishi / "web"
        cls.gree = cls.dist / "data" / "brands" / "gree"
        cls.gree_web = cls.gree / "web"
        cls.panasonic = cls.dist / "data" / "brands" / "panasonic"
        cls.panasonic_web = cls.panasonic / "web"
        cls.midea = cls.dist / "data" / "brands" / "midea"
        cls.midea_web = cls.midea / "web"
        cls.lg = cls.dist / "data" / "brands" / "lg"
        cls.lg_web = cls.lg / "web"
        cls.haier = cls.dist / "data" / "brands" / "haier"
        cls.haier_web = cls.haier / "web"
        cls.samsung = cls.dist / "data" / "brands" / "samsung"
        cls.samsung_web = cls.samsung / "web"
        cls.toshiba = cls.dist / "data" / "brands" / "toshiba"
        cls.toshiba_web = cls.toshiba / "web"
        cls.hisense = cls.dist / "data" / "brands" / "hisense"
        cls.hisense_web = cls.hisense / "web"
        cls.tcl = cls.dist / "data" / "brands" / "tcl"
        cls.tcl_web = cls.tcl / "web"
        cls.mhi = cls.dist / "data" / "brands" / "mitsubishi-heavy-industries"
        cls.mhi_web = cls.mhi / "web"
        cls.aux = cls.dist / "data" / "brands" / "aux-air"
        cls.aux_web = cls.aux / "web"
        cls.roca = cls.dist / "data" / "brands" / "roca-clima"
        cls.roca_web = cls.roca / "web"
        cls.airwell = cls.dist / "data" / "brands" / "airwell-historica"
        cls.airwell_web = cls.airwell / "web"

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_expected_counts(self):
        manifest = load(self.dist / "data" / "brands" / "index.json")
        brands = {item["slug"]: item for item in manifest["brands"]}
        self.assertEqual(
            set(brands),
            {"airwell-historica", "aux-air", "daikin", "fujitsu-general", "gree", "haier", "hisense", "lg", "midea", "mitsubishi-electric", "mitsubishi-heavy-industries", "panasonic", "roca-clima", "samsung", "tcl", "toshiba"},
        )
        self.assertEqual(brands["fujitsu-general"]["counts"], {
            "categories": 18,
            "topics": 39,
            "variants": 71,
            "errors": 117,
            "search_entries": 188,
        })
        self.assertEqual(brands["daikin"]["counts"], {
            "categories": 13,
            "topics": 14,
            "variants": 34,
            "errors": 66,
            "search_entries": 100,
        })
        self.assertEqual(brands["mitsubishi-electric"]["counts"], {
            "categories": 15,
            "topics": 22,
            "variants": 56,
            "errors": 107,
            "search_entries": 163,
        })
        self.assertEqual(brands["gree"]["counts"], {
            "categories": 15,
            "topics": 22,
            "variants": 81,
            "errors": 179,
            "search_entries": 260,
        })
        self.assertEqual(brands["panasonic"]["counts"], {
            "categories": 15,
            "topics": 25,
            "variants": 108,
            "errors": 127,
            "search_entries": 235,
        })
        self.assertEqual(brands["midea"]["counts"], {
            "categories": 15,
            "topics": 24,
            "variants": 86,
            "errors": 222,
            "search_entries": 308,
        })
        self.assertEqual(brands["lg"]["counts"], {
            "categories": 15,
            "topics": 23,
            "variants": 64,
            "errors": 81,
            "search_entries": 145,
        })
        self.assertEqual(brands["haier"]["counts"], {
            "categories": 15,
            "topics": 24,
            "variants": 67,
            "errors": 120,
            "search_entries": 187,
        })
        self.assertEqual(brands["samsung"]["counts"], {
            "categories": 16,
            "topics": 31,
            "variants": 72,
            "errors": 119,
            "search_entries": 191,
        })
        self.assertEqual(brands["toshiba"]["counts"], {
            "categories": 16,
            "topics": 34,
            "variants": 80,
            "errors": 122,
            "search_entries": 202,
        })
        self.assertEqual(brands["hisense"]["counts"], {
            "categories": 16,
            "topics": 37,
            "variants": 107,
            "errors": 114,
            "search_entries": 221,
        })
        self.assertEqual(brands["tcl"]["counts"], {
            "categories": 16,
            "topics": 28,
            "variants": 67,
            "errors": 105,
            "search_entries": 172,
        })
        self.assertEqual(brands["mitsubishi-heavy-industries"]["counts"], {
            "categories": 16,
            "topics": 35,
            "variants": 100,
            "errors": 110,
            "search_entries": 210,
        })
        self.assertEqual(brands["aux-air"]["counts"], {
            "categories": 16,
            "topics": 37,
            "variants": 107,
            "errors": 98,
            "search_entries": 205,
        })
        self.assertEqual(brands["roca-clima"]["counts"], {
            "categories": 16,
            "topics": 30,
            "variants": 76,
            "errors": 79,
            "search_entries": 155,
        })
        self.assertEqual(brands["airwell-historica"]["counts"], {
            "categories": 17,
            "topics": 34,
            "variants": 91,
            "errors": 40,
            "search_entries": 131,
        })

    def test_search_examples_are_present(self):
        entries = load(self.web / "search.json")
        for query in ("pump down", "boya", "Peak Cut", "mando 2 hilos"):
            with self.subTest(query=query):
                self.assertTrue(contains_query(entries, query))

        errors = load(self.web / "errors" / "index.json")
        token = normalized("E12")
        self.assertTrue(any(token in item.get("search_text", "") for item in errors))

        daikin_entries = load(self.daikin_web / "search.json")
        for query in (
            "A3", "AF", "pump down", "flotador", "BRC1E", "VRV IV",
            "E9 X21A", "Madoka P1 P2", "Wiring Error Check SW3",
        ):
            with self.subTest(brand="daikin", query=query):
                self.assertTrue(contains_query(daikin_entries, query))

        daikin_errors = load(self.daikin_web / "errors" / "index.json")
        self.assertEqual(len(daikin_errors), 66)
        self.assertTrue({
            "A0-11", "A3", "AF", "E3", "E9", "J8", "U3", "U4", "UA", "E-1",
        }.issubset({item["code_display"] for item in daikin_errors}))

        mitsubishi_entries = load(self.mitsubishi_web / "search.json")
        for query in (
            "P5 boya 90 segundos",
            "P5 parada 5 segundos cuatro veces",
            "PAR-41 8,5 12 VDC",
            "SW871 10 15 minutos",
            "6607 sin ACK",
            "1102 125",
            "M-NET 17 30 VDC",
            "POWER 11 bus continua",
            "pump down",
        ):
            with self.subTest(brand="mitsubishi-electric", query=query):
                self.assertTrue(contains_query(mitsubishi_entries, query))

        mitsubishi_errors = load(self.mitsubishi_web / "errors" / "index.json")
        self.assertEqual(len(mitsubishi_errors), 107)

        gree_entries = load(self.gree_web / "search.json")
        for query in (
            "E9 8 segundos boya",
            "COM N 56 VDC",
            "A2 10 min",
            "XK46 C01 3 segundos",
            "n6 cinco",
            "C9 120 h",
            "NTC 20 25",
            "IPM 0.3 0.7",
            "n8 30 min",
            "Commissioning Tool MC40-00/B",
            "A8 24 h",
            "15k NTC 1.65 V",
            "U-Match E3 tres estados",
            "FLEXX ULTRA FE EA",
            "FLEXX IPM PFC 0.3 0.7",
            "sensor presion 30 segundos",
        ):
            with self.subTest(brand="gree", query=query):
                self.assertTrue(contains_query(gree_entries, query))

        gree_errors = load(self.gree_web / "errors" / "index.json")
        self.assertEqual(len(gree_errors), 179)
        self.assertTrue({
            "A2", "A8", "C0", "C5", "dH", "E6", "E9", "F0", "H5",
            "L3", "P8", "U7", "FE", "EH", "CA", "Cb", "LE",
        }.issubset({item["code_display"] for item in gree_errors}))

        panasonic_entries = load(self.panasonic_web / "search.json")
        for query in (
            "H11 12 A 30 segundos",
            "H11 comunicacion",
            "P10 boya",
            "CZ-RTC6 R1 R2 500 m",
            "Assigning 10 min",
            "S-LINK 30 120 ohm",
            "Test Run 60 min",
            "pump down",
            "EEV 46 4 ohm",
            "ventilador 280 VDC",
            "NTC 20k Beta 3950",
            "P04 3.3 2.6 MPa",
            "bomba 0001 0060",
            "H&C Diagnosis",
            "J07 R32",
            "respaldo automatico CHECK",
            "CV6231785082",
            "ocho alarmas exteriores",
            "item 80 item 81",
            "F16 3.03 MPa",
            "zona tres minutos Thermo Off",
        ):
            with self.subTest(brand="panasonic", query=query):
                self.assertTrue(contains_query(panasonic_entries, query))

        panasonic_errors = load(self.panasonic_web / "errors" / "index.json")
        self.assertEqual(len(panasonic_errors), 127)
        self.assertTrue({
            "E01", "E04", "H11", "H12", "H21", "P04", "P10", "P12",
            "F29", "F31", "J07", "J08", "CHECK",
        }.issubset({item["code_display"] for item in panasonic_errors}))

        self.assertTrue({
            "P5", "PA", "E6", "U2", "0403", "1102", "1302", "4250",
            "5101", "6607", "6832", "7102", "POWER ×11",
        }.issubset({item["code_display"] for item in mitsubishi_errors}))

        midea_entries = load(self.midea_web / "search.json")
        for query in (
            "A11 fuga R454B ventilador maxima",
            "WDC-120T2 10 fallos",
            "ON OFF velocidad 7 s",
            "X1 X2 200 m",
            "3 min 30 s",
            "cassette boya 3 min calor",
            "b36 5 min",
            "P Q E 0,75 1200 m",
            "System Test 240 minutos",
            "n1-2-0 pump down",
            "PC03 4,4 0,13 MPa",
            "24V 12V 5V 3,3V",
            "d51 presion estatica 3 7 min",
            "d72 respaldo 7 dias",
            "bus DC 277 410",
            "E3 ventilador interior",
            "E8 control central ventilador",
            "E8 comunicacion twin",
        ):
            with self.subTest(brand="midea", query=query):
                self.assertTrue(contains_query(midea_entries, query))

        midea_errors = load(self.midea_web / "errors" / "index.json")
        self.assertEqual(len(midea_errors), 222)
        self.assertTrue({
            "A01", "A11", "C21", "C51", "b36", "EH0E", "EL01",
            "PC03", "PC0L", "U3A", "1L46", "d51", "d72", "E3", "E8",
        }.issubset({item["code_display"] for item in midea_errors}))

        haier_entries = load(self.haier_web / "search.json")
        for query in (
            "E7 15 comunicacion",
            "29 1D baja presion",
            "boya calor 2 s",
            "YR-E16B 35",
            "YR-E17 tres hilos",
            "CC n2 n3 PS",
            "LL HH",
            "10K 23K 50K",
            "alarma no detiene 78",
            "CN4 220",
            "555.3 ambiente",
            "ventilador 310 334",
        ):
            with self.subTest(brand="haier", query=query):
                self.assertTrue(contains_query(haier_entries, query))

        haier_errors = load(self.haier_web / "errors" / "index.json")
        self.assertEqual(len(haier_errors), 120)
        self.assertTrue({
            "E7", "E14", "F1", "F36", "15", "26-0", "29", "1D",
            "39-0", "71-1", "78", "555.0", "555.3", "08", "0C", "Lo",
        }.issubset({item["code_display"] for item in haier_errors}))

        samsung_entries = load(self.samsung_web / "search.json")
        for query in (
            "E199 K1 K5",
            "E201 dial interiores",
            "E203 rojo fijo verde fijo naranja parpadea",
            "E604 mando 12 V",
            "E153 boya bomba",
            "K2 pump down K7",
            "SNET 60 minutos",
            "pilotos amarillo verde rojo",
            "option code todos pilotos parpadean",
            "E206 C003 inverter PBA",
            "triple evacuacion 5000 2000 200",
        ):
            with self.subTest(brand="samsung", query=query):
                self.assertTrue(contains_query(samsung_entries, query))

        samsung_errors = load(self.samsung_web / "errors" / "index.json")
        self.assertEqual(len(samsung_errors), 119)
        self.assertTrue({
            "E101", "E153", "E163", "E199", "E201", "E203",
            "E206-C003", "E416", "E458", "E464", "E500", "E604", "UP", "dF",
        }.issubset({item["code_display"] for item in samsung_errors}))

        toshiba_entries = load(self.toshiba_web / "search.json")
        for query in (
            "04 comunicacion 15 60 V",
            "P10 boya 4 minutos",
            "D800 D805 F04",
            "SW81 SW82 refrigerant collection",
            "RBC AMTU31 A B 18 V",
            "001 O DN 007 20000 horas",
            "or recuperacion aceite",
            "desescarche cooperativo 01D 01E 01F",
            "F08 continua funcionamiento",
            "52 codigos 7F",
        ):
            with self.subTest(brand="toshiba", query=query):
                self.assertTrue(contains_query(toshiba_entries, query))

        toshiba_errors = load(self.toshiba_web / "errors" / "index.json")
        self.assertEqual(len(toshiba_errors), 122)
        self.assertTrue({
            "04", "1C", "20", "E01", "E04", "E09", "F04", "F08",
            "H01", "L29", "P10", "P20", "001", "022", "or", "dF",
        }.issubset({item["code_display"] for item in toshiba_errors}))

        hisense_entries = load(self.hisense_web / "search.json")
        for query in (
            "SLEEP diez veces",
            "HIGH POWER cinco veces",
            "LED2 300 900",
            "RUN DEFROST decenas unidades",
            "PSW1 PSW3 cinco segundos",
            "no01 no15 historial",
            "emergencia ocho horas",
            "P06 0,2 MPa",
            "boya 01 51",
            "Hi Checker tarjeta SD",
            "auto addressing tres minutos cinco",
        ):
            with self.subTest(brand="hisense", query=query):
                self.assertTrue(contains_query(hisense_entries, query))

        hisense_errors = load(self.hisense_web / "errors" / "index.json")
        self.assertEqual(len(hisense_errors), 114)
        self.assertTrue({
            "01", "03", "04", "16", "31", "35", "43", "51", "53",
            "64", "70", "C1", "C3", "EE", "E4", "E8", "E36",
            "FE", "P01", "P06", "P0A", "P0d",
        }.issubset({item["code_display"] for item in hisense_errors}))

        tcl_entries = load(self.tcl_web / "search.json")
        for query in (
            "ECO ocho veces ocho segundos",
            "E8 11 destellos exterior",
            "LED exterior 0,5 3 s",
            "cassette LED1 LED4",
            "boya 8 s 180 s 10 min",
            "Mode Up cinco segundos",
            "P3 RS485",
            "CAN 2000 m 100 kbps",
            "respaldo compresor",
            "WIREDCASCTRL todos iconos 3 s",
            "310 V 15 V ventilador",
        ):
            with self.subTest(brand="tcl", query=query):
                self.assertTrue(contains_query(tcl_entries, query))

        tcl_errors = load(self.tcl_web / "errors" / "index.json")
        self.assertEqual(len(tcl_errors), 105)
        self.assertTrue({
            "E0", "E4", "E8", "E9", "EE", "EF", "FE", "P0", "P1",
            "P5", "D3", "C0", "C5", "Fb", "Fn",
            "1 destello exterior", "17 destello exterior",
        }.issubset({item["code_display"] for item in tcl_errors}))

        mhi_entries = load(self.mhi_web / "search.json")
        for query in (
            "RUN TIMER 42",
            "pulso inicial 1,5 s 11 s",
            "E9 boya 3 s 10 s",
            "pump down 0,087 MPa",
            "E5 normal pump down",
            "RC-EX3 dos hilos no polarizado",
            "P31 direccionamiento automatico",
            "SW3-7 frio calor forzado",
            "Mente PC 30 minutos",
            "E54-2 alta presion PSH",
            "E37-5 subenfriamiento",
            "LED amarillo 9 destellos",
        ):
            with self.subTest(brand="mitsubishi-heavy-industries", query=query):
                self.assertTrue(contains_query(mhi_entries, query))

        mhi_errors = load(self.mhi_web / "errors" / "index.json")
        self.assertEqual(len(mhi_errors), 110)
        self.assertTrue({
            "01", "05", "35", "42", "61", "62", "80", "84",
            "E1", "E5", "E9", "E19", "E35", "E41", "E45", "E59",
            "E36-1", "E37-5", "E43-2", "E54-2", "E58-1", "WAIT",
        }.issubset({item["code_display"] for item in mhi_errors}))

        aux_entries = load(self.aux_web / "search.json")
        for query in (
            "D1 D2 D3",
            "E8 display placa",
            "E8 temperatura exterior",
            "E8 sonda descarga",
            "H1 drenaje alta presion",
            "CHECK ARV",
            "12V GND A B",
            "bomba cassette A5",
            "9 destellos E9",
            "black box 30 minutos",
            "50K 3950",
            "bus 420 642 V",
            "SWING FUNCTION 5 segundos",
            "CL TIMER 5 segundos",
        ):
            with self.subTest(brand="aux-air", query=query):
                self.assertTrue(contains_query(aux_entries, query))

        aux_errors = load(self.aux_web / "errors" / "index.json")
        self.assertEqual(len(aux_errors), 98)
        self.assertTrue({
            "E0", "E4", "E5", "5E", "E8", "E9", "EA", "Eb",
            "F0", "F1", "F8", "H1", "H2", "H4", "J2", "J3",
            "A5", "AA", "AE", "AJ", "P2", "P3", "L0", "LA",
            "31", "36", "47",
        }.issubset({item["code_display"] for item in aux_errors}))

    def test_media_is_not_published_or_referenced(self):
        self.assertFalse((self.brand / "media").exists())
        self.assertFalse((self.daikin / "media").exists())
        self.assertFalse((self.mitsubishi / "media").exists())
        self.assertFalse((self.gree / "media").exists())
        self.assertFalse((self.panasonic / "media").exists())
        self.assertFalse((self.midea / "media").exists())
        self.assertFalse((self.haier / "media").exists())
        self.assertFalse((self.samsung / "media").exists())
        self.assertFalse((self.toshiba / "media").exists())
        self.assertFalse((self.hisense / "media").exists())
        self.assertFalse((self.tcl / "media").exists())
        self.assertFalse((self.mhi / "media").exists())
        self.assertFalse((self.aux / "media").exists())
        self.assertEqual(self.report["checks"]["media_files"], 0)
        self.assertGreaterEqual(self.report["checks"]["media_references_removed"], 26)

        for path in (
            list(self.web.rglob("*.json"))
            + list(self.daikin_web.rglob("*.json"))
            + list(self.mitsubishi_web.rglob("*.json"))
            + list(self.gree_web.rglob("*.json"))
            + list(self.panasonic_web.rglob("*.json"))
            + list(self.midea_web.rglob("*.json"))
            + list(self.haier_web.rglob("*.json"))
            + list(self.samsung_web.rglob("*.json"))
            + list(self.toshiba_web.rglob("*.json"))
            + list(self.hisense_web.rglob("*.json"))
            + list(self.tcl_web.rglob("*.json"))
            + list(self.mhi_web.rglob("*.json"))
            + list(self.aux_web.rglob("*.json"))
        ):
            data = load(path)
            pending = [data]
            while pending:
                node = pending.pop()
                if isinstance(node, dict):
                    if "media" in node:
                        self.assertEqual(node["media"], [], path)
                    pending.extend(node.values())
                elif isinstance(node, list):
                    pending.extend(node)

    def test_forbidden_server_files_are_absent(self):
        forbidden_suffixes = {".db", ".sqlite", ".sqlite3", ".php", ".py", ".md"}
        for path in self.dist.rglob("*"):
            if path.is_file():
                self.assertNotIn(path.suffix.lower(), forbidden_suffixes, path)
                self.assertNotEqual(path.name.lower(), ".htaccess")

    def test_browser_uses_static_data_provider(self):
        portal = (self.dist / "index.html").read_text(encoding="utf-8")
        html = (self.dist / "climatizacion.html").read_text(encoding="utf-8")
        script = (self.dist / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("climatizacion.html", portal)
        self.assertIn("smd.html", portal)
        self.assertIn("assets/app.js", html)
        self.assertIn("data/brands/index.json", script)
        self.assertNotIn("api.php", html + script)
        self.assertNotIn("media.php", html + script)
        self.assertIn("renderLedPatternTable", script)
        self.assertIn("led-pattern-table", script)
        self.assertIn("renderRelatedErrors", script)
        self.assertIn("renderIndicationContexts", script)
        self.assertIn("El código puede cambiar según dónde se lea", script)
        self.assertIn("function localizedText", script)
        self.assertIn("record.translations?.[language]?.[field]", script)

    def test_beta_multilingual_shell_and_feedback_are_public(self):
        pages = {
            name: (self.dist / name).read_text(encoding="utf-8")
            for name in ("index.html", "climatizacion.html", "smd.html", "feedback.html")
        }
        for name, html in pages.items():
            with self.subTest(page=name):
                self.assertIn("assets/common.css", html)
                self.assertIn("assets/i18n.js", html)
                self.assertIn("BETA", html)

        i18n = (self.dist / "assets" / "i18n.js").read_text(encoding="utf-8")
        feedback = (self.dist / "assets" / "feedback.js").read_text(encoding="utf-8")
        for language in ("es", "en", "pt", "fr"):
            self.assertIn(f"{language}:", i18n)
        for marker in (
            "st.language",
            "st:languagechange",
            "common.translationScope",
            "feedback.html?page=",
            "Versión beta pública",
            "Public beta version",
            "Versão beta pública",
            "Version bêta publique",
        ):
            self.assertIn(marker, i18n)
        self.assertIn("mailto:info@replacor.com", feedback)
        self.assertNotIn("fetch(", feedback)
        self.assertIn('id="feedbackForm"', pages["feedback.html"])
        self.assertIn("https://www.replacor.com/", pages["feedback.html"])

    def test_samsung_led_tables_are_structured_and_accessible(self):
        topic = load(self.samsung_web / "topics" / "1.json")
        self.assertEqual(topic["slug"], "rac-outdoor-led-master")
        self.assertEqual(len(topic["variants"][0]["led_patterns"]), 25)
        self.assertEqual(len(topic["variants"][1]["led_patterns"]), 27)

        allowed_states = {"on", "off", "blink", "fast_blink", "slow_blink", "pulse", "alternate"}
        for variant in topic["variants"]:
            for pattern in variant["led_patterns"]:
                self.assertEqual(
                    [row["label"] for row in pattern["led_indicators"]],
                    ["Amarillo", "Verde", "Rojo"],
                )
                self.assertTrue(all(row["state"] in allowed_states for row in pattern["led_indicators"]))
                self.assertTrue(pattern["relationship"])
                self.assertTrue(pattern["family_hint"])

        details = [
            load(path)
            for path in self.samsung_web.joinpath("errors", "details").glob("*.json")
        ]
        e203 = next(row for row in details if row["code_display"] == "E203")
        led_contexts = [
            context
            for interpretation in e203["interpretations"]
            for context in interpretation["indication_contexts"]
            if context.get("led_indicators")
        ]
        self.assertTrue(any(
            [row["label"] for row in context["led_indicators"]] == ["Rojo", "Verde", "Naranja"]
            and [row["state"] for row in context["led_indicators"]] == ["on", "on", "blink"]
            for context in led_contexts
        ))

    def test_toshiba_reference_v1_led_tables_quality_and_code_layers(self):
        topic = load(self.toshiba_web / "topics" / "1.json")
        self.assertEqual(topic["slug"], "toshiba-six-led-master")
        self.assertEqual([len(item["led_patterns"]) for item in topic["variants"]], [27, 27, 31])

        allowed_states = {"on", "off", "blink", "fast_blink", "slow_blink", "pulse", "alternate"}
        for variant in topic["variants"]:
            for pattern in variant["led_patterns"]:
                self.assertEqual(
                    [row["label"] for row in pattern["led_indicators"]],
                    ["D800", "D801", "D802", "D803", "D804", "D805"],
                )
                self.assertTrue(all(row["state"] in allowed_states for row in pattern["led_indicators"]))
                self.assertTrue(pattern["relationship"])
                self.assertTrue(pattern["family_hint"])

        details = [
            load(path)
            for path in self.toshiba_web.joinpath("errors", "details").glob("*.json")
        ]
        e01 = next(item for item in details if item["code_display"] == "E01")
        self.assertEqual(len(e01["interpretations"]), 2)
        code_1c = next(item for item in details if item["code_display"] == "1C")
        self.assertGreaterEqual(len(code_1c["interpretations"]), 5)
        p10 = next(item for item in details if item["code_display"] == "P10")
        self.assertEqual(len(p10["interpretations"]), 2)

        expected = audit_brand(ROOT / "data" / "brands" / "toshiba")
        actual = load(ROOT / "data" / "brands" / "toshiba" / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 176})
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 80})
        self.assertEqual(actual["errors"]["component_coverage"]["exact_page"], {"count": 176, "percent": 100.0})

    def test_hisense_reference_v1_led_tables_quality_and_code_layers(self):
        topic = load(self.hisense_web / "topics" / "1.json")
        self.assertEqual(topic["slug"], "legacy-outdoor-led-table")
        patterns = topic["variants"][0]["led_patterns"]
        self.assertEqual(len(patterns), 18)
        self.assertEqual([item["code_display"] for item in patterns], [str(value) for value in range(1, 19)])
        for pattern in patterns:
            self.assertEqual(pattern["led_indicators"], [{
                "label": "LED2", "color": "red", "state": "blink",
            }])
            self.assertIn("300 ms", pattern["counting_rule"])
            self.assertIn("900 ms", pattern["cycle_note"])

        details = [
            load(path)
            for path in self.hisense_web.joinpath("errors", "details").glob("*.json")
        ]
        code_16 = next(item for item in details if item["code_display"] == "16")
        self.assertEqual(len(code_16["interpretations"]), 4)
        code_31 = next(item for item in details if item["code_display"] == "31")
        self.assertEqual(len(code_31["interpretations"]), 3)
        code_51 = next(item for item in details if item["code_display"] == "51")
        self.assertEqual(len(code_51["interpretations"]), 2)
        c3 = next(item for item in details if item["code_display"] == "C3")
        self.assertEqual(c3["interpretations"][0]["title"], "Interior de otro ciclo conectada a la caja selectora")

        expected = audit_brand(ROOT / "data" / "brands" / "hisense")
        actual = load(ROOT / "data" / "brands" / "hisense" / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 159})
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 107})
        self.assertEqual(actual["errors"]["component_coverage"]["exact_page"], {"count": 159, "percent": 100.0})

    def test_tcl_reference_v1_led_tables_quality_and_code_layers(self):
        outdoor_topic = load(self.tcl_web / "topics" / "1.json")
        self.assertEqual(outdoor_topic["slug"], "outdoor-blink-table")
        patterns = outdoor_topic["variants"][0]["led_patterns"]
        self.assertEqual(len(patterns), 17)
        self.assertEqual([item["code_display"] for item in patterns], [str(value) for value in range(1, 18)])
        for pattern in patterns:
            self.assertEqual(pattern["led_indicators"][0]["label"], "LED exterior")
            self.assertEqual(pattern["led_indicators"][0]["state"], "pulse")
            self.assertIn("0,5 s", pattern["counting_rule"])
            self.assertIn("3 s", pattern["cycle_note"])

        cassette_topic = load(self.tcl_web / "topics" / "2.json")
        self.assertEqual(cassette_topic["slug"], "cassette-four-led-table")
        cassette_patterns = cassette_topic["variants"][0]["led_patterns"]
        self.assertGreaterEqual(len(cassette_patterns), 12)
        self.assertTrue(all(
            [row["label"] for row in pattern["led_indicators"]] == ["LED1", "LED2", "LED3", "LED4"]
            for pattern in cassette_patterns
        ))

        details = [
            load(path)
            for path in self.tcl_web.joinpath("errors", "details").glob("*.json")
        ]
        e4 = next(item for item in details if item["code_display"] == "E4")
        self.assertEqual(len(e4["interpretations"]), 3)
        ee = next(item for item in details if item["code_display"] == "EE")
        self.assertEqual(len(ee["interpretations"]), 2)
        fe = next(item for item in details if item["code_display"] == "FE")
        self.assertEqual(len(fe["interpretations"]), 2)
        p1 = next(item for item in details if item["code_display"] == "P1")
        self.assertEqual(len(p1["interpretations"]), 2)

        expected = audit_brand(ROOT / "data" / "brands" / "tcl")
        actual = load(ROOT / "data" / "brands" / "tcl" / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 111})
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 67})
        self.assertEqual(actual["errors"]["component_coverage"]["exact_page"], {"count": 111, "percent": 100.0})

    def test_mhi_reference_v1_led_tables_quality_and_code_layers(self):
        rac_topic = load(self.mhi_web / "topics" / "2.json")
        self.assertEqual(rac_topic["slug"], "rac-run-timer-table")
        rac_patterns = rac_topic["variants"][0]["led_patterns"]
        self.assertEqual(len(rac_patterns), 23)
        code_42 = next(item for item in rac_patterns if item["code_display"] == "42")
        self.assertEqual(
            [(row["label"], row["state"], row["detail"]) for row in code_42["led_indicators"]],
            [("RUN", "pulse", "4 destellos"), ("TIMER", "pulse", "2 destellos")],
        )
        self.assertIn("1,5 s", code_42["counting_rule"])
        self.assertIn("11 s", code_42["cycle_note"])

        pac_topic = load(self.mhi_web / "topics" / "3.json")
        self.assertEqual(pac_topic["slug"], "pac-led-table")
        pac_patterns = pac_topic["variants"][0]["led_patterns"]
        self.assertEqual(len(pac_patterns), 18)
        e42_pattern = next(item for item in pac_patterns if item["code_display"] == "E42")
        self.assertEqual(
            [(row["label"], row["state"]) for row in e42_pattern["led_indicators"]],
            [
                ("LED rojo control", "pulse"),
                ("LED verde control", "blink"),
                ("LED amarillo inverter", "pulse"),
            ],
        )
        self.assertEqual(e42_pattern["led_indicators"][2]["detail"], "9 destellos")

        details = [
            load(path)
            for path in self.mhi_web.joinpath("errors", "details").glob("*.json")
        ]
        for code in ("E5", "E9", "E38", "E42", "E45", "E48", "E53", "E59"):
            row = next(item for item in details if item["code_display"] == code)
            self.assertEqual(len(row["interpretations"]), 2, code)
        e54_2 = next(item for item in details if item["code_display"] == "E54-2")
        self.assertIn("alta presión", e54_2["interpretations"][0]["title"])

        expected = audit_brand(ROOT / "data" / "brands" / "mitsubishi-heavy-industries")
        actual = load(ROOT / "data" / "brands" / "mitsubishi-heavy-industries" / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 128})
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 100})
        self.assertEqual(actual["errors"]["component_coverage"]["exact_page"], {"count": 128, "percent": 100.0})

        sources = load(self.mhi_web / "sources.json")
        self.assertEqual(len(sources), 9)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        public_text = "\n".join(path.read_text(encoding="utf-8") for path in self.mhi.rglob("*.json"))
        self.assertNotIn("tmp\\pdfs\\mhi", public_text)
        self.assertNotIn("tmp/text/mhi", public_text)
        self.assertFalse(any(self.mhi.rglob("*.pdf")))
        self.assertFalse(any(self.mhi.rglob("*.db")))
        self.assertFalse(any(self.mhi.rglob("*.sqlite")))

    def test_aux_reference_v1_led_tables_quality_and_code_layers(self):
        split_topic = load(self.aux_web / "topics" / "2.json")
        self.assertEqual(split_topic["slug"], "split-d1-d2-d3-master")
        split_patterns = split_topic["variants"][0]["led_patterns"]
        self.assertEqual(len(split_patterns), 27)
        self.assertEqual(
            [row["code_display"] for row in split_patterns],
            [f"Patrón {value:02d}" for value in range(1, 28)],
        )
        pattern_10 = next(row for row in split_patterns if row["code_display"] == "Patrón 10")
        self.assertEqual(
            [(row["label"], row["state"]) for row in pattern_10["led_indicators"]],
            [("D1", "blink"), ("D2", "on"), ("D3", "on")],
        )

        commercial_topic = load(self.aux_web / "topics" / "3.json")
        self.assertEqual(commercial_topic["slug"], "commercial-led-master")
        self.assertEqual([len(row["led_patterns"]) for row in commercial_topic["variants"]], [7, 6])
        e9_high = next(
            row
            for row in commercial_topic["variants"][1]["led_patterns"]
            if row["code_display"] == "E9 alta"
        )
        self.assertEqual(
            [row["detail"] for row in e9_high["led_indicators"]],
            ["9 destellos y 2 s apagado", "1 destello y 2 s apagado"],
        )

        arv_topic = load(self.aux_web / "topics" / "4.json")
        self.assertEqual(arv_topic["slug"], "arv-indicator-code")
        arv_patterns = arv_topic["variants"][0]["led_patterns"]
        self.assertEqual(len(arv_patterns), 9)
        self.assertEqual(
            [row["code_display"] for row in arv_patterns],
            ["A1–AF", "C1–CF", "E1–EF", "H1–HF", "F1–FF", "J1–JF", "31–3F", "41–4F", "51–5F"],
        )

        details = [
            load(path)
            for path in self.aux_web.joinpath("errors", "details").glob("*.json")
        ]
        e8 = next(row for row in details if row["code_display"] == "E8")
        self.assertEqual(len(e8["interpretations"]), 3)
        self.assertTrue(any("display" in row["title"].lower() for row in e8["interpretations"]))
        self.assertTrue(any("temperatura exterior" in row["title"].lower() for row in e8["interpretations"]))
        self.assertTrue(any("descarga" in row["title"].lower() for row in e8["interpretations"]))

        for code, minimum in (("E1", 3), ("E3", 4), ("F1", 3), ("H1", 2), ("H4", 2)):
            row = next(item for item in details if item["code_display"] == code)
            self.assertGreaterEqual(len(row["interpretations"]), minimum, code)

        expected = audit_brand(ROOT / "data" / "brands" / "aux-air")
        actual = load(ROOT / "data" / "brands" / "aux-air" / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 142})
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 107})
        self.assertEqual(actual["errors"]["component_coverage"]["exact_page"], {"count": 142, "percent": 100.0})

        sources = load(self.aux_web / "sources.json")
        self.assertEqual(len(sources), 8)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        public_text = "\n".join(path.read_text(encoding="utf-8") for path in self.aux.rglob("*.json"))
        self.assertNotIn("tmp\\aux", public_text)
        self.assertNotIn("tmp/aux", public_text)
        self.assertFalse(any(self.aux.rglob("*.pdf")))
        self.assertFalse(any(self.aux.rglob("*.db")))
        self.assertFalse(any(self.aux.rglob("*.sqlite")))

    def test_roca_reference_v1_provenance_codes_and_operational_effects(self):
        quality = load(self.roca_web / "quality.json")
        self.assertEqual(quality, audit_brand(ROOT / "data" / "brands" / "roca-clima"))
        self.assertEqual(quality["errors"]["status_counts"], {"complete": 92})
        self.assertEqual(quality["technical_variants"]["status_counts"], {"complete": 76})

        provenance = load(self.roca_web / "provenance.json")
        self.assertEqual(provenance["policy_version"], "1.0")
        self.assertTrue(any(
            item["status"] == "accepted_explicit_manufacturer"
            and item["family"] == "YCSA/YCSA-H 50/60 T/TP"
            and item["page"] == "55"
            for item in provenance["accepted"]
        ))
        self.assertTrue(provenance["excluded"])

        sources = load(self.roca_web / "sources.json")
        self.assertEqual(len(sources), 8)
        self.assertTrue({
            "N-27134-1003",
            "INF-27426",
            "DPC-1-INSTALLATION-OPERATION",
            "N-27344-1204M",
            "Y-R61063-1104",
            "YCSA-120-180-TECHNICAL",
            "ROCA-HISTORY-2005-HVAC-SALE",
            "BORME-C-2007-16073",
        }.issubset({source["document_ref"] for source in sources}))

        errors = {item["code_display"]: item for item in load(self.roca_web / "errors" / "index.json")}
        self.assertEqual(errors["1-1"]["interpretation_count"], 2)
        self.assertEqual(errors["2-4"]["interpretation_count"], 2)
        self.assertTrue({
            "1", "1-1", "4-4", "11", "45", "91", "93", "99",
            "E1", "EE", "FL", "H1", "L2", "d1", "r2", "Cn",
        }.issubset(errors))

        green = load(self.roca_web / "topics" / "2.json")
        self.assertEqual(len(green["variants"][0]["led_patterns"]), 16)
        red = load(self.roca_web / "topics" / "3.json")
        self.assertEqual(len(red["variants"][0]["led_patterns"]), 6)
        self.assertEqual(len(red["variants"][1]["led_patterns"]), 15)

        topics = [load(path) for path in self.roca_web.joinpath("topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "Código propio 91-99",
            "AVO: cuatro formas documentadas de rearme",
            "Alarma seria ID1",
            "Térmico de bomba ID4/ID18",
            "Incidencia verde AVO",
            "Parada parcial/total YCSA",
            "Fabricante explícito",
            "Equipos posteriores a la venta",
        }.issubset(titles | {topic["title"] for topic in topics}))

        search = load(self.roca_web / "search.json")
        for query in (
            "piloto verde 1-1",
            "piloto rojo alta presión",
            "DPC 93 comunicación",
            "YLCC FL caudal",
            "YCSA bomba reserva",
            "fabricante Clima Roca York",
            "equipos posteriores marcas blancas",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

        public_text = "\n".join(path.read_text(encoding="utf-8") for path in self.roca.rglob("*.json"))
        self.assertNotIn("tmp\\pdfs\\roca", public_text)
        self.assertFalse(any(self.roca.rglob("*.pdf")))
        self.assertFalse(any(self.roca.rglob("*.db")))
        self.assertFalse(any(self.roca.rglob("*.sqlite")))

    def test_airwell_historical_reference_v1_provenance_codes_and_service_data(self):
        quality = load(self.airwell_web / "quality.json")
        self.assertEqual(
            quality,
            audit_brand(ROOT / "data" / "brands" / "airwell-historica"),
        )
        self.assertEqual(quality["errors"]["status_counts"], {"complete": 167})
        self.assertEqual(quality["technical_variants"]["status_counts"], {"complete": 91})
        self.assertEqual(
            quality["errors"]["component_coverage"]["exact_page"],
            {"count": 167, "percent": 100.0},
        )

        provenance = load(self.airwell_web / "provenance.json")
        self.assertEqual(provenance["policy_version"], "1.0")
        self.assertTrue(any(
            item["status"] == "accepted_explicit_manufacturer"
            and item["family"] == "HRW 07-12"
            and item["page"] == "40"
            for item in provenance["accepted"]
        ))
        self.assertTrue(any(
            item["status"] == "accepted_historic_own_manufacturing_era"
            and "TRIO/QUATTRO" in item["family"]
            for item in provenance["accepted"]
        ))
        self.assertTrue(provenance["excluded"])

        sources = load(self.airwell_web / "sources.json")
        self.assertEqual(len(sources), 7)
        self.assertTrue({
            "SM BS DCI 1-A.1 GB",
            "SM DLSRPM 1-A.4 GB",
            "SM DUODCI 1-A.1 GB",
            "SM TQDCI 1-A.1 GB",
            "IOM HRW 02-N-7F / 3990404",
            "AIRWELL-CATALOGUE-2017-GB",
            "AIRWELL-DEPLIANT-GAMME-FR-0425-V11",
        }.issubset({source["document_ref"] for source in sources}))

        errors = {
            item["code_display"]: item
            for item in load(self.airwell_web / "errors" / "index.json")
        }
        self.assertEqual(errors["1"]["interpretation_count"], 7)
        self.assertEqual(errors["3"]["interpretation_count"], 7)
        self.assertEqual(errors["11"]["interpretation_count"], 7)
        self.assertEqual(errors["21"]["interpretation_count"], 5)
        self.assertEqual(errors["111111110"]["interpretation_count"], 2)
        self.assertTrue({
            "1", "3", "11", "21", "29", "30", "31",
            "100000000", "111100000", "111111110", "111111111",
        }.issubset(errors))

        topics = [
            load(path) for path in self.airwell_web.joinpath("topics").glob("*.json")
        ]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "Tabla interior BS",
            "Exterior MSMP",
            "Tabla exterior 1-30",
            "Tabla modo frío",
            "Entrada por mando",
            "Advertencia de protección",
            "Desbordamiento con unidad ON",
            "Puertos A-D",
            "Ventilador exterior BLDC",
            "Fabricante explícito HRW",
            "Equipos posteriores a 2008",
        }.issubset(titles))

        search = load(self.airwell_web / "search.json")
        for query in (
            "MODE RESET diagnóstico BS",
            "MSMP once LED",
            "HMI tres dígitos puertos A D",
            "DLS autoprueba mando 16 grados",
            "desbordamiento DNC unidad OFF",
            "HRW 111111110 flotador",
            "270 V sobretensión TQ",
            "Airwell Industrie France fabricante",
            "equipos posteriores 2008 origen no acreditado",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

        public_text = "\n".join(
            path.read_text(encoding="utf-8") for path in self.airwell.rglob("*.json")
        )
        self.assertNotIn("tmp\\pdfs\\airwell", public_text)
        self.assertNotIn("tmp/pdfs/airwell", public_text)
        self.assertFalse(any(self.airwell.rglob("*.pdf")))
        self.assertFalse(any(self.airwell.rglob("*.db")))
        self.assertFalse(any(self.airwell.rglob("*.sqlite")))

    def test_field_navigation_uses_dashboard_accordions_and_quick_search(self):
        html = (self.dist / "climatizacion.html").read_text(encoding="utf-8")
        script = (self.dist / "assets" / "app.js").read_text(encoding="utf-8")
        styles = (self.dist / "assets" / "styles.css").read_text(encoding="utf-8")

        for marker in (
            'id="homeButton"', 'id="brandStatus"', 'class="menu-navigation"',
            'class="app-logo"', 'assets/super-tecnico-logo.png',
            'id="quickAccessPanel"', 'Selecciona la marca',
            'class="resource-strip resource-strip-public"', 'Libro Gree y Midea',
            'Libro técnico gratuito', 'Abrir libro completo',
            'recursos/libro-electronica-inverter-replacor.pdf',
            'data-ad-placement="home"', 'data-ad-placement="after-content"',
            'data-quick-query="sacar códigos"', 'data-quick-query="mando 2 hilos"',
        ):
            self.assertIn(marker, html)
        for marker in (
            "renderBrandDashboard", "renderQuickAccess", "rememberRecent", "data-open-category",
            "Consultado recientemente", "¿Qué necesitas hacer?",
            "quickErrorSelect", "errorCatalogSelect", "errorCatalogOptions",
            "No se ha eliminado información.", "todos los temas, errores, procedimientos",
            "hasMultipleInterpretations", "Ninguno está preseleccionado.",
            "machine_behavior", "Cómo reconocerlo", "En frío o deshumidificación",
        ):
            self.assertIn(marker, script)
        self.assertNotIn("await selectCategory(remembered)", script)
        self.assertTrue((self.dist / "assets" / "super-tecnico-logo.png").is_file())
        self.assertTrue((self.dist / "assets" / "libro-electronica-inverter-replacor-portada.png").is_file())
        self.assertTrue((self.dist / "recursos" / "libro-electronica-inverter-replacor.pdf").is_file())
        for marker in (
            ".category-grid", ".category-card", ".quick-actions", ".recent-panel",
            ".info-priority", ".quick-error-form", ".task-grid", ".library-explorer",
            ".resource-strip", ".ad-slot[hidden]",
        ):
            self.assertIn(marker, styles)

    def test_smd_catalog_is_public_safe_complete_and_ambiguous(self):
        catalog = load(self.dist / "data" / "smd" / "catalog.json")
        meta = catalog["meta"]
        candidates = catalog["candidates"]
        self.assertEqual(meta["candidate_count"], 439)
        self.assertEqual(meta["manufacturer_count"], 6)
        self.assertEqual(meta["identification_ready"], 439)
        self.assertEqual(meta["exact_ambiguity_groups"], 13)
        self.assertEqual(len(candidates), 439)
        self.assertEqual(len({item["id"] for item in candidates}), 439)
        self.assertTrue(all(
            item["quality"]["level"] == "identification_ready"
            and item["quality"]["marking_verified"]
            and item["quality"]["package_verified"]
            and item["quality"]["pinout_verified"]
            and item["quality"]["electrical_data_verified"]
            and item["marking"]["layouts"]
            and item["package"]["name"]
            and item["package"]["pins"]
            and item["pinout"]
            and item["parameters"]
            and item["source"]["url"].startswith("https://")
            and item["source"]["datasheet_url"].startswith("https://")
            for item in candidates
        ))

        markings = {item["marking"]["core"] for item in candidates}
        for marking in ("K38", "K72", "AIs", "K224", "Z1"):
            self.assertIn(marking, markings)
        z1 = [
            item for item in candidates
            if item["marking"]["core"] == "Z1" and item["package"]["name"] == "SOT-23"
        ]
        self.assertEqual(len(z1), 2)

        public_text = json.dumps(catalog, ensure_ascii=False).lower()
        self.assertNotIn("smd codebook", public_text)
        self.assertNotIn("historical candidate", public_text)

        html = (self.dist / "smd.html").read_text(encoding="utf-8")
        script = (self.dist / "assets" / "smd.js").read_text(encoding="utf-8")
        self.assertIn('id="smdSearchForm"', html)
        self.assertIn("data/smd/catalog.json", script)
        self.assertIn("smd.resultsIntro", script)
        self.assertIn("directKinds", script)
        self.assertNotIn("<details class=\"candidate-card\" open", script)

    def test_error_finder_explains_current_coverage(self):
        script = (self.dist / "assets" / "app.js").read_text(encoding="utf-8")
        self.assertIn("O elegir de la lista completa", script)
        self.assertIn("Selecciona un código de error", script)
        self.assertIn("todavía no está incluido en la base", script)
        self.assertIn("no puede mostrar una ficha que aún no se ha cargado", script)
        self.assertIn("limit:500", script)

    def test_daikin_projection_keeps_private_master_data_out(self):
        public_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in self.daikin.rglob("*.json")
        )
        self.assertNotIn("drive_id", public_text)
        self.assertNotIn("drive_title", public_text)
        self.assertNotIn("modelos_ocultos", public_text)
        self.assertNotIn("1uuiYPbdPX75iZNp2zBLjCQ8M8E3sxodh", public_text)
        self.assertFalse(any(self.daikin.rglob("*.sqlite")))
        self.assertFalse(any(self.daikin.rglob("*.db")))

        topics = [load(path) for path in (self.daikin_web / "topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        self.assertEqual(len(variants), 34)
        self.assertTrue(all(
            variant["steps"]
            and variant["sections"]
            and any(source.get("page_start") for source in variant["sources"])
            for variant in variants
        ))

    def test_daikin_reference_v2_quality_and_traceability(self):
        brand = ROOT / "data" / "brands" / "daikin"
        expected = audit_brand(brand)
        actual = load(brand / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 66)
        self.assertEqual(actual["errors"]["interpretations"], 118)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 118})
        self.assertEqual(actual["technical_variants"]["entries"], 34)
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 34})

        sources = load(brand / "web" / "sources.json")
        self.assertEqual(len(sources), 9)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        self.assertTrue({
            "ESiES06-07", "ESiEN05-04", "SiUS121602E", "4P370475-1",
            "4PW71264-1", "4P596266-1B", "4P486046-1C",
        }.issubset({source["document_ref"] for source in sources}))

        interpretations = []
        for path in (brand / "web" / "errors" / "details").glob("*.json"):
            interpretations.extend(load(path)["interpretations"])
        self.assertTrue(all(
            {"cause", "check", "machine_behavior"}.issubset(
                {item["item_type"] for item in interpretation["info_items"]}
            )
            and any(source.get("page_start") for source in interpretation["sources"])
            for interpretation in interpretations
        ))

    def test_daikin_key_procedures_and_subcodes_are_present(self):
        web = ROOT / "data" / "brands" / "daikin" / "web"
        search = load(web / "search.json")
        for query in (
            "TIMER CANCEL 5 segundos",
            "BRC7E830 pitido continuo",
            "BRC1E historial 10",
            "Madoka esclavo U5 U8",
            "RZAG BS2 8 segundos",
            "boya 80 segundos 10 minutos",
            "E9 Y2E X21A",
            "LC FAN2",
            "U3 operacion posible",
            "J8 todas las unidades",
            "sonda descarga 100 13.1",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

        errors = {item["code_display"]: item for item in load(web / "errors" / "index.json")}
        self.assertGreaterEqual(errors["E9"]["interpretation_count"], 4)
        self.assertGreaterEqual(errors["U3"]["interpretation_count"], 3)
        self.assertGreaterEqual(errors["J8"]["interpretation_count"], 2)

    def test_mitsubishi_reference_v1_quality_and_traceability(self):
        brand = ROOT / "data" / "brands" / "mitsubishi-electric"
        expected = audit_brand(brand)
        actual = load(brand / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 107)
        self.assertEqual(actual["errors"]["interpretations"], 142)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 142})
        self.assertEqual(actual["technical_variants"]["entries"], 56)
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 56})

        sources = load(brand / "web" / "sources.json")
        self.assertEqual(len(sources), 12)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        self.assertTrue({
            "OBH766B", "OBH767", "OBH790P", "OCH697", "OCH416D",
            "OCH832B", "OCH675E", "WT09534X02", "WT05000X01",
            "WT06591X01",
        }.issubset({source["document_ref"] for source in sources}))

        interpretations = []
        for path in (brand / "web" / "errors" / "details").glob("*.json"):
            interpretations.extend(load(path)["interpretations"])
        self.assertTrue(all(
            {"cause", "check", "machine_behavior"}.issubset(
                {item["item_type"] for item in interpretation["info_items"]}
            )
            and any(source.get("page_start") for source in interpretation["sources"])
            for interpretation in interpretations
        ))

    def test_mitsubishi_key_diagnostics_are_separated_by_family(self):
        brand = ROOT / "data" / "brands" / "mitsubishi-electric"
        web = brand / "web"
        errors = {item["code_display"]: item for item in load(web / "errors" / "index.json")}
        self.assertEqual(errors["P5"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["U2"]["interpretation_count"], 3)
        self.assertEqual(errors["POWER ×1"]["interpretation_count"], 2)
        self.assertEqual(errors["POWER ×2"]["interpretation_count"], 2)
        self.assertEqual(errors["POWER ×3"]["interpretation_count"], 2)
        self.assertEqual(errors["POWER ×11"]["interpretation_count"], 2)

        topics = [
            load(path)
            for path in (web / "topics").glob("*.json")
        ]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "Cassette — autocheck inalámbrico por pitidos",
            "PAR-41MAA — Remote controller check",
            "Cassette antigua — P5 por boya durante 90 segundos",
            "Cassette moderna — P5 por parada repetida del motor",
            "MXZ de 2 conexiones — corrección por 30 min en frío",
            "MXZ de 3–6 conexiones — botón SW871",
            "Alcance de parada: interior frente a BC/exterior",
            "M-NET — forma de onda, ruido y pantalla",
        }.issubset(titles))
        self.assertTrue(all(
            variant["steps"]
            and variant["sections"]
            and variant["media"] == []
            and any(source.get("page_start") for source in variant["sources"])
            for variant in variants
        ))

        public_text = "\n".join(path.read_text(encoding="utf-8") for path in brand.rglob("*.json"))
        self.assertNotIn("tmp/pdfs", public_text)
        self.assertFalse(any(brand.rglob("*.pdf")))
        self.assertFalse(any(brand.rglob("*.db")))
        self.assertFalse(any(brand.rglob("*.sqlite")))

    def test_gree_reference_v2_quality_and_traceability(self):
        brand = ROOT / "data" / "brands" / "gree"
        expected = audit_brand(brand)
        actual = load(brand / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 179)
        self.assertEqual(actual["errors"]["interpretations"], 225)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 225})
        self.assertEqual(actual["technical_variants"]["entries"], 81)
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 81})

        sources = load(brand / "web" / "sources.json")
        self.assertEqual(len(sources), 16)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        self.assertTrue({
            "ENVO-R32-SM-A", "LIVO-GEN3-SM-230V-A", "VIREO-GEN3-SM-A",
            "SLIM-DUCT-SM-A", "GMV5-MINI-HP-SM", "GMV5-IDU-SM",
            "GMV6-UH-MINI-SM", "XK19-TPG", "XK46-OM", "XK62-XK79-OM",
            "U-MATCH-PLUS-SM-B", "GREE-FLEXX-INDOOR-OUTDOOR-SM-092821",
            "GC202301-I", "GC202406-I",
        }.issubset({source["document_ref"] for source in sources}))

        interpretations = []
        for path in (brand / "web" / "errors" / "details").glob("*.json"):
            interpretations.extend(load(path)["interpretations"])
        self.assertTrue(all(
            {"cause", "check", "machine_behavior"}.issubset(
                {item["item_type"] for item in interpretation["info_items"]}
            )
            and any(source.get("page_start") for source in interpretation["sources"])
            for interpretation in interpretations
        ))

    def test_gree_repeated_codes_and_service_procedures_are_separated(self):
        brand = ROOT / "data" / "brands" / "gree"
        web = brand / "web"
        errors = {item["code_display"]: item for item in load(web / "errors" / "index.json")}
        self.assertGreaterEqual(errors["E9"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["C5"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["F0"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["H5"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["L3"]["interpretation_count"], 2)

        topics = [load(path) for path in (web / "topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "XK46 — localizar interior y leer errores con C01",
            "GMV6 — consultar las cinco últimas averías con n6",
            "Split inverter — diagnóstico COM–N (~56 VDC)",
            "GMV6 — A2 recuperación desde tuberías interiores",
            "GMV6 — C9 emergencia de un ventilador",
            "Cassette R32 — E9 tras 8 s de boya abierta",
            "Sistema modular — aislar un módulo exterior averiado",
            "GMV6 — prueba de diodos del IPM",
        }.issubset(titles))
        self.assertTrue(all(
            variant["steps"]
            and variant["sections"]
            and variant["media"] == []
            and any(source.get("page_start") for source in variant["sources"])
            for variant in variants
        ))

        public_text = "\n".join(path.read_text(encoding="utf-8") for path in brand.rglob("*.json"))
        self.assertNotIn("tmp/pdfs", public_text)
        self.assertFalse(any(brand.rglob("*.pdf")))
        self.assertFalse(any(brand.rglob("*.db")))
        self.assertFalse(any(brand.rglob("*.sqlite")))

    def test_panasonic_reference_v2_quality_and_traceability(self):
        brand = ROOT / "data" / "brands" / "panasonic"
        expected = audit_brand(brand)
        actual = load(brand / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 127)
        self.assertEqual(actual["errors"]["interpretations"], 183)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 183})
        self.assertEqual(actual["technical_variants"]["entries"], 108)
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 108})

        sources = load(brand / "web" / "sources.json")
        self.assertEqual(len(sources), 21)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        self.assertTrue({
            "PAPAMY1212045CE", "SM700885-00", "PAPAMY1505100CE",
            "PAPAMY2509044CE", "ECOI-VRF-CODE-GUIDE", "SM830186-00",
            "W-2WAY-ECOI-SM", "U-8_24MS3H7-II-EN",
            "WEB-ACXF60-38393-EN", "EU-4P-CZ-RTC6-CONEX-20",
            "SM830188-00", "CZ-RTC2-OM-9L", "PAPAMY2509043CE",
            "VRF-GEN-26-LR",
        }.issubset({source["document_ref"] for source in sources}))

        interpretations = []
        for path in (brand / "web" / "errors" / "details").glob("*.json"):
            interpretations.extend(load(path)["interpretations"])
        self.assertTrue(all(
            {"cause", "check", "machine_behavior"}.issubset(
                {item["item_type"] for item in interpretation["info_items"]}
            )
            and any(source.get("page_start") for source in interpretation["sources"])
            for interpretation in interpretations
        ))

    def test_gree_and_panasonic_v2_publish_honest_coverage_matrices(self):
        for slug, expected_sources in (("gree", 16), ("panasonic", 21)):
            with self.subTest(brand=slug):
                brand = ROOT / "data" / "brands" / slug
                config = load(brand / "brand.json")
                navigation = load(brand / "web" / "navigation.json")
                matrix = load(brand / "web" / "coverage_matrix.json")
                coverage = load(brand / "web" / "coverage.json")

                self.assertEqual(config["data_version"], "2.0.0")
                self.assertEqual(navigation["metadata"]["data_version"], "2.0.0")
                self.assertEqual(matrix["counts"]["sources"], expected_sources)
                self.assertTrue(matrix["known_gaps"])
                self.assertIn("no se declara cobertura", matrix["coverage_basis"].lower())
                self.assertTrue(all(
                    item["coverage_status"] == "reference_v2_strong"
                    for item in coverage
                ))
                self.assertTrue(all(
                    family["status"] == "strong"
                    and family["sources"]
                    for family in matrix["families"]
                ))

    def test_panasonic_repeated_codes_and_service_procedures_are_separated(self):
        brand = ROOT / "data" / "brands" / "panasonic"
        web = brand / "web"
        errors = {item["code_display"]: item for item in load(web / "errors" / "index.json")}
        self.assertGreaterEqual(errors["H11"]["interpretation_count"], 3)
        self.assertGreaterEqual(errors["H12"]["interpretation_count"], 3)
        self.assertGreaterEqual(errors["H21"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["P10"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["P12"]["interpretation_count"], 2)

        topics = [load(path) for path in (web / "topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "Mando inalámbrico RAC — localizar el código con CHECK",
            "CZ-RTC6 — últimas cuatro alarmas y Sensor info",
            "ECOi actual — decodificar LED1 M y LED2 N",
            "CZ-RTC6 — bus R1/R2 de dos hilos sin polaridad",
            "S-LINK — resistencia de línea con alimentación cortada",
            "CZ-RTC6 — Test Run desde Maintenance func",
            "PACi — forzar bomba 1 minuto o funcionamiento continuo",
            "Multisplit — comprobar EEV: 46 ±4 Ω a 20 °C",
            "Códigos repetidos — H11, H12, H21, P10 y P12",
        }.issubset(titles))
        self.assertTrue(all(
            variant["steps"]
            and variant["sections"]
            and variant["media"] == []
            and any(source.get("page_start") for source in variant["sources"])
            for variant in variants
        ))

        public_text = "\n".join(path.read_text(encoding="utf-8") for path in brand.rglob("*.json"))
        self.assertNotIn("tmp/pdfs", public_text)
        self.assertFalse(any(brand.rglob("*.pdf")))
        self.assertFalse(any(brand.rglob("*.db")))
        self.assertFalse(any(brand.rglob("*.sqlite")))

    def test_midea_reference_v1_quality_and_traceability(self):
        brand = ROOT / "data" / "brands" / "midea"
        expected = audit_brand(brand)
        actual = load(brand / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 222)
        self.assertEqual(actual["errors"]["interpretations"], 227)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 227})
        self.assertEqual(actual["technical_variants"]["entries"], 86)
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 86})

        sources = load(brand / "web" / "sources.json")
        self.assertEqual(len(sources), 14)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        self.assertTrue({
            "SM-MIDEA-R454B-ATOMX-V2", "MIDEA-VRF-IDU-R454B-V5",
            "WDC-120T2-V1", "SM-AG11-R410A-3D-INV-220628",
            "SM-DLFSOAH", "SM-DLCMRHB", "MIDEA-V6-I-SERIES-IM",
            "MCAC-UTSM-201501", "MU-M-EXP-CONDUCTO-A6-ES",
            "MIDEA-ES-E3-FAN-DIAGNOSIS", "MIDEA-CCM30-MD12IU-028BW",
        }.issubset({source["document_ref"] for source in sources}))

        interpretations = []
        for path in (brand / "web" / "errors" / "details").glob("*.json"):
            interpretations.extend(load(path)["interpretations"])
        self.assertTrue(all(
            {"cause", "check", "machine_behavior"}.issubset(
                {item["item_type"] for item in interpretation["info_items"]}
            )
            and interpretation["indication_contexts"]
            and all(
                context.get("display_location")
                and context.get("family_hint")
                and context.get("source_document_ref")
                for context in interpretation["indication_contexts"]
            )
            and any(source.get("page_start") for source in interpretation["sources"])
            for interpretation in interpretations
        ))

        errors = {item["code_display"]: item for item in load(brand / "web" / "errors" / "index.json")}
        self.assertGreaterEqual(errors["C21"]["interpretation_count"], 2)
        self.assertGreaterEqual(errors["P52"]["interpretation_count"], 2)
        self.assertEqual(errors["E3"]["interpretation_count"], 1)
        self.assertEqual(errors["E8"]["interpretation_count"], 3)
        e3 = load(brand / "web" / "errors" / "details" / f"{errors['E3']['id']}.json")
        e8 = load(brand / "web" / "errors" / "details" / f"{errors['E8']['id']}.json")
        e3_interpretation = e3["interpretations"][0]
        self.assertEqual(
            {item["code_display"] for item in e3_interpretation["indication_contexts"]},
            {"E3", "E8"},
        )
        self.assertTrue(any(
            item["code_display"] == "E8"
            and item["related_error_id"] == errors["E8"]["id"]
            and "control" in item["display_location"].lower()
            for item in e3_interpretation["indication_contexts"]
        ))
        self.assertTrue(any(
            dataset["name"].startswith("Motor DC interior")
            and any(
                point.get("value_min") == 280 and point.get("value_max") == 380
                for point in dataset["points"]
            )
            for dataset in e3_interpretation["datasets"]
        ))
        self.assertTrue({
            "Dirección de exterior",
            "Velocidad del ventilador interior fuera de control — código del control",
            "Comunicación incorrecta entre dos unidades interiores",
        }.issubset({item["title"] for item in e8["interpretations"]}))

        topics = [load(path) for path in (brand / "web" / "topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "WDC-120T2 — registro de diez fallos",
            "Split mural — modo ingeniero del mando inalámbrico",
            "AtomX — Cooling System Test",
            "A11 — comportamiento automático por fuga",
            "Cassette de una vía — secuencia en calefacción",
            "Cassette de una vía — secuencia en refrigeración",
            "V6 — bus P/Q/E",
            "AtomX — fuentes auxiliares de placa",
            "Conductos — detección automática de presión estática",
            "E3 en la unidad / E8 en el control — ventilador interior",
        }.issubset(titles))
        self.assertTrue(all(
            variant["steps"]
            and variant["sections"]
            and variant["media"] == []
            and any(source.get("page_start") for source in variant["sources"])
            for variant in variants
        ))

        public_text = "\n".join(path.read_text(encoding="utf-8") for path in brand.rglob("*.json"))
        self.assertNotIn("C:\\tmp", public_text)
        self.assertFalse(any(brand.rglob("*.pdf")))
        self.assertFalse(any(brand.rglob("*.db")))
        self.assertFalse(any(brand.rglob("*.sqlite")))

    def test_all_json_is_utf8_and_valid(self):
        paths = list(self.dist.rglob("*.json"))
        self.assertGreaterEqual(len(paths), 165)
        for path in paths:
            load(path)

    def test_fujitsu_quality_audit_is_current(self):
        brand = ROOT / "data" / "brands" / "fujitsu-general"
        expected = audit_brand(brand)
        actual = load(brand / "web" / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 117)
        self.assertEqual(actual["errors"]["interpretations"], 127)
        self.assertEqual(actual["errors"]["technical_interpretations"], 118)
        self.assertEqual(actual["errors"]["status_counts"].get("complete"), 118)
        self.assertEqual(actual["errors"]["status_counts"].get("developed", 0), 0)
        self.assertEqual(actual["errors"]["status_counts"].get("partial", 0), 0)
        self.assertEqual(actual["errors"]["status_counts"].get("reference_only", 0), 0)
        self.assertEqual(actual["technical_variants"]["entries"], 71)
        self.assertEqual(actual["technical_variants"]["status_counts"].get("partial", 0), 0)
        self.assertEqual(actual["technical_variants"]["status_counts"].get("reference_only", 0), 0)

    def test_fujitsu_confirmation_only_duplicates_are_consolidated(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        expected = {
            3: 2, 5: 1, 7: 1, 9: 1, 11: 1, 12: 1, 13: 1, 14: 2, 15: 1,
            16: 1, 17: 1, 18: 2, 19: 1, 20: 1, 21: 1, 22: 1,
            23: 1, 25: 1, 26: 1, 28: 1, 29: 1, 30: 1, 31: 1, 32: 1,
        }
        for error_id, interpretation_count in expected.items():
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                self.assertEqual(len(detail["interpretations"]), interpretation_count)
                index = load(web / "errors" / "index.json")
                row = next(item for item in index if item["id"] == error_id)
                self.assertEqual(row["interpretation_count"], interpretation_count)

    def test_fujitsu_vrii_service_diagnostics_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 55)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 54)

        for error_id in range(69, 111):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = detail["interpretations"][0]
                item_types = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", item_types)
                self.assertIn("check", item_types)
                self.assertIn("machine_behavior", item_types)
                self.assertTrue(any(
                    source.get("document_ref") == "AIRSTAGE_VRII_SERVICE"
                    for source in interpretation["sources"]
                ))

        discharge_pressure = load(web / "errors" / "details" / "90.json")["interpretations"][0]
        curve = discharge_pressure["datasets"][0]
        self.assertEqual(curve["points"][0]["value_nominal"], 0.50)
        self.assertEqual(curve["points"][-1]["value_nominal"], 4.50)

        eev = load(web / "errors" / "details" / "99.json")["interpretations"][0]
        winding = eev["datasets"][0]["points"][0]
        self.assertEqual((winding["value_min"], winding["value_nominal"], winding["value_max"]), (42.0, 46.0, 50.0))

        fan = load(web / "errors" / "details" / "96.json")["interpretations"][0]
        self.assertEqual(fan["operational_impacts"][0]["stop_level"], "permanent_stop")

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "CN118 5 V"))
        self.assertTrue(contains_query(search, "EEV1 46 ohm"))

    def test_fujitsu_vrii_communications_and_addressing_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 66)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 24)

        for error_id in (40, 54, 55, 58, 59, 61, 62, 63, 64, 65, 66):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = detail["interpretations"][0]
                item_types = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", item_types)
                self.assertIn("check", item_types)
                self.assertIn("machine_behavior", item_types)
                self.assertTrue(any(
                    source.get("document_ref") == "AIRSTAGE_VRII_SERVICE"
                    for source in interpretation["sources"]
                ))

        remote = load(web / "errors" / "details" / "54.json")["interpretations"][0]
        self.assertEqual(remote["datasets"][0]["points"][0]["value_nominal"], 12.0)

        missing_indoor = load(web / "errors" / "details" / "64.json")["interpretations"][0]
        self.assertEqual(missing_indoor["operational_impacts"][0]["stop_level"], "all_system")
        self.assertIn("no se detiene", missing_indoor["operational_impacts"][0]["degraded_behavior"])

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "SET4 1 180 segundos"))
        self.assertTrue(contains_query(search, "CNC01 12 V"))

    def test_fujitsu_multisplit_check_run_is_complete(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 67)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 23)

        e15 = load(web / "errors" / "details" / "4.json")
        interpretation = next(item for item in e15["interpretations"] if item["id"] == 42)
        item_types = {item["item_type"] for item in interpretation["info_items"]}
        self.assertIn("cause", item_types)
        self.assertIn("check", item_types)
        self.assertIn("machine_behavior", item_types)
        self.assertTrue(any(
            source.get("document_ref") == "9374995530-05"
            for source in interpretation["sources"]
        ))

        topic = load(web / "topics" / "30.json")
        variant = topic["variants"][0]
        self.assertEqual(variant["id"], 47)
        self.assertGreaterEqual(len(variant["steps"]), 8)
        self.assertTrue(any("10 minutos" in step.get("instruction", "") for step in variant["steps"]))

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "CHECK RUN LED A F"))
        self.assertTrue(contains_query(search, "correccion automatica cableado"))

    def test_fujitsu_legacy_simultaneous_addressing_is_complete(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertGreaterEqual(quality["errors"]["status_counts"].get("complete", 0), 70)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 20)

        for error_id, interpretation_id in ((37, 43), (38, 45), (39, 46)):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = next(item for item in detail["interpretations"] if item["id"] == interpretation_id)
                item_types = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", item_types)
                self.assertIn("check", item_types)
                self.assertIn("machine_behavior", item_types)
                self.assertTrue(interpretation["datasets"])
                self.assertTrue(any(
                    source.get("document_ref") == "9374318445-06"
                    for source in interpretation["sources"]
                ))

        topic = load(web / "topics" / "31.json")
        variant = topic["variants"][0]
        self.assertEqual(variant["id"], 48)
        self.assertEqual({parameter["parameter_code"] for parameter in variant["parameters"]}, {"DIP R.C.", "02", "51", "DIP SW1-2"})
        rc = next(parameter for parameter in variant["parameters"] if parameter["parameter_code"] == "DIP R.C.")
        self.assertEqual(len(rc["options"]), 16)

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "funcion 02 circuito frigorifico"))
        self.assertTrue(contains_query(search, "funcion 51 principal secundaria"))

    def test_fujitsu_grouping_codes_route_to_complete_subcodes(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"
        quality = load(web / "quality.json")
        self.assertEqual(quality["errors"]["grouping_references"], 9)
        self.assertEqual(quality["errors"]["technical_interpretations"], 118)
        self.assertEqual(quality["errors"]["status_counts"].get("grouping_reference"), 9)
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 6)
        for component in quality["errors"]["component_coverage"].values():
            self.assertLessEqual(component["percent"], 100.0)

        expected = {
            44: {84},
            47: {87, 88},
            49: {99, 100, 101},
            50: {105, 106},
        }
        for error_id, target_ids in expected.items():
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                interpretation = detail["interpretations"][0]
                self.assertEqual(interpretation["entry_role"], "grouping_reference")
                self.assertEqual({item["id"] for item in interpretation["related_errors"]}, target_ids)
                self.assertTrue(interpretation["routing_note"])
                for target_id in target_ids:
                    self.assertTrue((web / "errors" / "details" / f"{target_id}.json").exists())

        search = load(web / "search.json")
        self.assertTrue(contains_query(search, "E75 E75 1 sonda aspiracion"))
        self.assertTrue(contains_query(search, "E9A E9A 3 bobina expansion"))

    def test_fujitsu_indoor_damper_power_and_valve_diagnostics(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        for error_id in (111, 112, 113):
            with self.subTest(error_id=error_id):
                interpretation = load(web / "errors" / "details" / f"{error_id}.json")["interpretations"][0]
                kinds = {item["item_type"] for item in interpretation["info_items"]}
                self.assertIn("cause", kinds)
                self.assertIn("check", kinds)
                self.assertTrue(any(source.get("document_ref") == "AOHG18_24KBTA3_SERVICE" for source in interpretation["sources"]))

        e57 = load(web / "errors" / "details" / "41.json")
        self.assertEqual(len(e57["interpretations"]), 2)
        self.assertTrue(all(
            {"cause", "check"}.issubset({item["item_type"] for item in interpretation["info_items"]})
            for interpretation in e57["interpretations"]
        ))

        e76 = load(web / "errors" / "details" / "45.json")
        self.assertEqual(len(e76["interpretations"]), 2)
        for interpretation in e76["interpretations"]:
            self.assertEqual(len(interpretation["datasets"]), 2)
            resistance = interpretation["datasets"][0]
            voltage = interpretation["datasets"][1]
            self.assertEqual(next(point["value_nominal"] for point in resistance["points"] if point["variable_value"] == 25), 10.0)
            self.assertEqual(next(point["value_nominal"] for point in voltage["points"] if point["variable_value"] == 25), 3.97)
            self.assertTrue(any("5,0 V" in item["body"] for item in interpretation["info_items"]))

        e612 = load(web / "errors" / "details" / "68.json")["interpretations"][0]
        values = [point["value_nominal"] for point in e612["datasets"][0]["points"]]
        self.assertEqual(values, [342, 400, 456])

        topic = load(web / "topics" / "32.json")
        self.assertEqual({variant["id"] for variant in topic["variants"]}, {49, 50})
        self.assertTrue(all(not variant["media"] for variant in topic["variants"]))

        search = load(web / "search.json")
        for query in ("E26 direccion duplicada", "CN18 compuerta", "E76 sonda valvula 5 V", "E61 2 342 V"):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_indoor_safety_and_symptom_diagnostics(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        e45 = load(web / "errors" / "details" / "114.json")
        self.assertEqual(len(e45["interpretations"]), 2)
        self.assertEqual(
            {item["operational_impacts"][0]["stop_level"] for item in e45["interpretations"]},
            {"all_system", "degraded"},
        )
        self.assertTrue(all(
            any(source.get("document_ref") == "AOHG18_24KBTA3_SERVICE" for source in item["sources"])
            for item in e45["interpretations"]
        ))

        e58 = load(web / "errors" / "details" / "115.json")["interpretations"][0]
        self.assertTrue(any("CN11" in item["body"] for item in e58["info_items"]))
        self.assertTrue({"cause", "check"}.issubset({item["item_type"] for item in e58["info_items"]}))

        ea8 = load(web / "errors" / "details" / "116.json")["interpretations"][0]
        self.assertEqual(ea8["operational_impacts"][0]["stop_level"], "all_system")
        self.assertIn("ventilación", ea8["operational_impacts"][0]["degraded_behavior"])
        self.assertIn("no puede detenerse", ea8["description"])

        symptom = load(web / "topics" / "33.json")
        self.assertEqual({item["id"] for item in symptom["variants"]}, set(range(51, 57)))
        no_operation = next(item for item in symptom["variants"] if item["id"] == 53)
        self.assertTrue(any("CN14" in section["body"] and "CNC01" in section["body"] for section in no_operation["sections"]))
        self.assertTrue(any("13 V" in (step.get("expected_result") or "") for step in no_operation["steps"]))

        components = load(web / "topics" / "34.json")
        self.assertEqual({item["id"] for item in components["variants"]}, {57, 58})
        self.assertTrue(all(not item["media"] for item in components["variants"]))

        search = load(web / "search.json")
        for query in (
            "E45 sensor deteriorado",
            "EA8 ventilacion seguridad",
            "E58 CN11 microinterruptor",
            "198 264 V sin alimentacion",
            "no enfria strainer",
            "fuga agua desague",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_eeprom_subcooler_and_second_fan_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        for error_id, page in ((7, "03-25"), (15, "03-40")):
            with self.subTest(error_id=error_id):
                detail = load(web / "errors" / "details" / f"{error_id}.json")
                self.assertEqual(len(detail["interpretations"]), 1)
                interpretation = detail["interpretations"][0]
                kinds = {item["item_type"] for item in interpretation["info_items"]}
                self.assertTrue({"cause", "check"}.issubset(kinds))
                self.assertTrue(any(
                    source.get("document_ref") == "AOHG18_24KBTA3_SERVICE" and source.get("page_start") == page
                    for source in interpretation["sources"]
                ))

        e62 = load(web / "errors" / "details" / "15.json")["interpretations"][0]
        self.assertEqual({item["id"] for item in e62["related_errors"]}, {70, 71, 72})

        e82 = load(web / "errors" / "details" / "46.json")["interpretations"][0]
        self.assertEqual(e82["entry_role"], "grouping_reference")
        self.assertEqual({item["id"] for item in e82["related_errors"]}, {86, 117})

        e821 = load(web / "errors" / "details" / "117.json")["interpretations"][0]
        self.assertTrue(any("CN142" in item["body"] and "5–6" in item["body"] for item in e821["info_items"]))
        curve = e821["datasets"][0]
        self.assertEqual(next(point["value_nominal"] for point in curve["points"] if point["variable_value"] == 25), 4.8)
        self.assertTrue(any(source.get("document_ref") == "AIRSTAGE_JII_SERVICE" for source in e821["sources"]))

        e98 = load(web / "errors" / "details" / "48.json")["interpretations"][0]
        self.assertEqual(e98["operational_impacts"][0]["stop_level"], "permanent_stop")
        power, control = e98["datasets"][0]["points"]
        self.assertEqual((power["value_min"], power["value_max"]), (280.0, 373.0))
        self.assertEqual((control["value_min"], control["value_nominal"], control["value_max"]), (13.5, 15.0, 16.5))

        topic = load(web / "topics" / "35.json")
        self.assertEqual({item["id"] for item in topic["variants"]}, {59, 60})
        self.assertTrue(all(not item["media"] for item in topic["variants"]))

        search = load(web / "search.json")
        for query in (
            "E32 EEPROM corrosion",
            "E62 6 comunicacion inverter",
            "E82 1 CN142 5 6",
            "E98 CN802 280 373",
            "segundo ventilador parada permanente",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_two_wire_controller_internal_errors_are_developed(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        for error_id in (53, 56, 57, 60):
            with self.subTest(error_id=error_id):
                interpretation = load(web / "errors" / "details" / f"{error_id}.json")["interpretations"][0]
                kinds = {item["item_type"] for item in interpretation["info_items"]}
                self.assertTrue({"cause", "check"}.issubset(kinds))
                self.assertTrue(any(
                    source.get("document_ref") == "UTY_RCRYZ1_IM_9373328483"
                    for source in interpretation["sources"]
                ))
                self.assertTrue(any("12 V" in item["body"] or "F1" in item["body"] for item in interpretation["info_items"]))

        data_error = load(web / "errors" / "details" / "57.json")["interpretations"][0]
        self.assertIn("unidad interior", data_error["description"])
        master_error = load(web / "errors" / "details" / "60.json")["interpretations"][0]
        self.assertTrue(any("exactamente un mando" in item["body"] for item in master_error["info_items"]))

        topic = load(web / "topics" / "36.json")
        self.assertEqual({item["id"] for item in topic["variants"]}, {61, 62, 63, 64})
        self.assertTrue(all(item["steps"] and item["sections"] for item in topic["variants"]))
        self.assertTrue(all(not item["media"] for item in topic["variants"]))

        quality = load(web / "quality.json")
        self.assertLessEqual(quality["errors"]["status_counts"].get("reference_only", 0), 2)

        search = load(web / "search.json")
        for query in (
            "C2 1 PCB transmision this product",
            "12 4 arranque Monitor Mode",
            "15 4 adquisicion datos direccion",
            "27 1 maestro esclavo F1 06",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_display_io_and_branch_box_errors_are_complete(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        e6a = load(web / "errors" / "details" / "43.json")
        self.assertIn("E6A.1", {item["alias_display"] for item in e6a["aliases"]})
        e6a_interpretation = e6a["interpretations"][0]
        self.assertTrue({"cause", "check", "machine_behavior"}.issubset(
            {item["item_type"] for item in e6a_interpretation["info_items"]}
        ))
        self.assertEqual(e6a_interpretation["datasets"][0]["points"][0]["value_nominal"], 10)
        self.assertTrue(any(
            source.get("document_ref") == "AOU48RLXFZ1_HYBRID_FLEX_SERVICE"
            and source.get("page_start") == "02-64"
            for source in e6a_interpretation["sources"]
        ))

        ed2 = load(web / "errors" / "details" / "51.json")
        self.assertTrue({"J2", "E.J2.U"}.issubset({item["alias_display"] for item in ed2["aliases"]}))
        ed2_interpretation = ed2["interpretations"][0]
        led_map = ed2_interpretation["datasets"][0]["points"]
        self.assertEqual(len(led_map), 10)
        self.assertTrue(any(point["variable_value"] == "LED402: 8 + LED403/404/405" and "EEV" in point["value_text"] for point in led_map))
        self.assertTrue(any("no afirma" in item["body"] for item in ed2_interpretation["info_items"]))

        e6a_topic = load(web / "topics" / "37.json")
        branch_topic = load(web / "topics" / "38.json")
        self.assertEqual({item["id"] for item in e6a_topic["variants"]}, {65})
        self.assertEqual({item["id"] for item in branch_topic["variants"]}, {66, 67, 68})
        self.assertTrue(all(not item["media"] for item in e6a_topic["variants"] + branch_topic["variants"]))

        quality = load(web / "quality.json")
        self.assertEqual(quality["errors"]["status_counts"].get("reference_only", 0), 0)
        self.assertEqual(quality["errors"]["status_counts"].get("complete"), 118)

        search = load(web / "search.json")
        for query in (
            "E6A 1 PCB I O 10 segundos",
            "J2 LED401 LED402 caja primaria",
            "LED402 8 EEV puerto A B C",
            "ED2 cantidad cajas CHECK RUN",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_e84_and_e95_duplicates_are_consolidated(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        e84 = load(web / "errors" / "details" / "24.json")
        self.assertEqual(len(e84["interpretations"]), 1)
        e84_interpretation = e84["interpretations"][0]
        self.assertEqual(e84_interpretation["operational_impacts"][0]["stop_level"], "permanent_stop")
        e84_text = " ".join(
            [e84_interpretation["description"]]
            + [item["body"] for item in e84_interpretation["info_items"]]
        )
        self.assertIn("0 A", e84_text)
        self.assertIn("56 rps", e84_text)
        self.assertTrue(any(
            source.get("document_ref") == "AOEH09KMCG"
            for source in e84_interpretation["sources"]
        ))

        e95 = load(web / "errors" / "details" / "27.json")
        self.assertEqual(len(e95["interpretations"]), 2)
        e95_text = " ".join(
            [item["title"] + " " + item["description"] for item in e95["interpretations"]]
            + [info["body"] for item in e95["interpretations"] for info in item["info_items"]]
        )
        for expected in ("30 intentos", "90", "40 segundos", "cinco veces"):
            self.assertIn(expected, e95_text)

        topic = load(web / "topics" / "39.json")
        self.assertEqual({item["id"] for item in topic["variants"]}, {69, 70, 71})
        self.assertTrue(all(not item["media"] for item in topic["variants"]))

        quality = load(web / "quality.json")
        self.assertEqual(quality["errors"]["status_counts"].get("partial", 0), 0)
        self.assertEqual(quality["errors"]["status_counts"].get("reference_only", 0), 0)

        search = load(web / "search.json")
        for query in (
            "E84 0 A 56 rps",
            "E95 10 3 30 sobrecorriente",
            "E95 rotor 90 40 segundos",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_normal_status_and_board_buttons_are_complete(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        board = load(web / "topics" / "5.json")["variants"][0]
        self.assertEqual(board["id"], 6)
        self.assertGreaterEqual(len(board["sections"]), 4)
        self.assertGreaterEqual(len(board["steps"]), 6)
        board_text = " ".join(
            [board["summary"]]
            + [item["body"] for item in board["sections"]]
            + [item["instruction"] for item in board["steps"]]
            + [item["expected_result"] or "" for item in board["steps"]]
        )
        for expected in ("S134", "S130", "EXIT", "electricidad estática", "no es una tecla de retroceso"):
            self.assertIn(expected, board_text)
        self.assertTrue(any(
            source.get("document_ref") == "AOEG22KATA"
            and source.get("page_start") == "05-6"
            and source.get("page_end") == "05-8"
            for source in board["sources"]
        ))

        status = load(web / "topics" / "24.json")["variants"][0]
        self.assertEqual(status["id"], 37)
        self.assertGreaterEqual(len(status["sections"]), 4)
        self.assertGreaterEqual(len(status["steps"]), 5)
        self.assertFalse(status["media"])
        options = status["parameters"][0]["options"]
        self.assertEqual({item["option_value"] for item in options}, {"CL", "Ht", "or", "dF", "PC", "Ln", "Sn"})
        status_text = " ".join(
            [status["summary"]]
            + [item["body"] for item in status["sections"]]
            + [item["instruction"] for item in status["steps"]]
        )
        self.assertIn("no errores por sí solos", status["summary"])
        self.assertIn("prefijo E", status_text)
        self.assertIn("recuperación de aceite", status_text)

        quality = load(web / "quality.json")
        self.assertEqual(quality["technical_variants"]["status_counts"], {"complete": 71})

        search = load(web / "search.json")
        for query in (
            "S134 S130 no pulsar pump down",
            "CL Ht or dF estados normales",
            "PC Ln Sn limitacion",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_all_technical_errors_have_documented_behavior_or_values(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        technical_count = 0
        for path in (web / "errors" / "details").glob("*.json"):
            detail = load(path)
            for interpretation in detail["interpretations"]:
                if interpretation.get("entry_role") == "grouping_reference":
                    continue
                technical_count += 1
                kinds = {item["item_type"] for item in interpretation.get("info_items", [])}
                self.assertTrue({"cause", "check"}.issubset(kinds), (path, interpretation["id"]))
                self.assertTrue(
                    "machine_behavior" in kinds
                    or interpretation.get("operational_impacts")
                    or interpretation.get("datasets"),
                    (path, interpretation["id"]),
                )
                self.assertTrue(any(source.get("page_start") for source in interpretation["sources"]))
        self.assertEqual(technical_count, 118)

        e11_return = load(web / "errors" / "details" / "1.json")["interpretations"][0]
        e11_behavior = next(item for item in e11_return["info_items"] if item["item_type"] == "machine_behavior")
        self.assertIn("2 minutos", e11_behavior["body"])
        self.assertIn("15 segundos", e11_behavior["body"])

        e64 = load(web / "errors" / "details" / "17.json")["interpretations"][0]
        self.assertEqual(e64["operational_impacts"][0]["stop_level"], "permanent_stop")
        e97 = load(web / "errors" / "details" / "28.json")["interpretations"][0]
        self.assertTrue(any(
            item["item_type"] == "machine_behavior" and "100 rpm" in item["body"] and "20 segundos" in item["body"]
            for item in e97["info_items"]
        ))

        quality = load(web / "quality.json")
        self.assertEqual(quality["errors"]["status_counts"], {"complete": 118, "grouping_reference": 9})
        self.assertEqual(quality["errors"]["component_coverage"]["operational_impacts"], {"count": 105, "percent": 89.0})

        search = load(web / "search.json")
        for query in (
            "E11 2 minutos 15 segundos",
            "E64 cinco repeticiones parada permanente",
            "E97 100 rpm 20 segundos",
            "A3 108 2 paradas 24 horas",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_fujitsu_all_technical_variants_have_steps_and_explanations(self):
        web = ROOT / "data" / "brands" / "fujitsu-general" / "web"

        variants = []
        for path in (web / "topics").glob("*.json"):
            topic = load(path)
            variants.extend(topic["variants"])
            for variant in topic["variants"]:
                self.assertTrue(variant["steps"], (path, variant["id"]))
                self.assertTrue(variant["sections"], (path, variant["id"]))
                self.assertTrue(any(source.get("page_start") for source in variant["sources"]), (path, variant["id"]))
        self.assertEqual(len(variants), 71)

        drain = load(web / "topics" / "16.json")["variants"]
        float_sequence = next(item for item in drain if item["id"] == 27)
        float_text = " ".join(
            [item["instruction"] + " " + (item["expected_result"] or "") for item in float_sequence["steps"]]
        )
        self.assertIn("frío/seco", float_text)
        self.assertIn("3 minutos", float_text)
        self.assertIn("sin extrapolar", float_text)

        buses = load(web / "topics" / "14.json")["variants"]
        two_wire = next(item for item in buses if item["id"] == 23)
        three_wire = next(item for item in buses if item["id"] == 24)
        self.assertTrue(any("no tiene polaridad" in item["instruction"] for item in two_wire["steps"]))
        self.assertTrue(any(
            "9C" in item["instruction"] or "9C" in (item["expected_result"] or "")
            for item in three_wire["steps"]
        ))

        resistance = next(item for item in load(web / "topics" / "20.json")["variants"] if item["id"] == 33)
        resistance_text = " ".join(item["instruction"] for item in resistance["steps"])
        for expected in ("0-50 Ω", "190 Ω-1 kΩ", "45-60 Ω"):
            self.assertIn(expected, resistance_text)

        quality = load(web / "quality.json")
        self.assertEqual(quality["technical_variants"]["status_counts"], {"complete": 71})

        search = load(web / "search.json")
        for query in (
            "bus 2WIRE blanco negro rojo aislado",
            "bus 3WIRE 9C reloj",
            "flotador frio seco 3 minutos sin extrapolar",
            "resistencia bus 0 50 cortocircuito",
            "Service Tool tendencias sobrecalentamiento presiones",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

    def test_lg_reference_v1_quality_traceability_and_key_diagnostics(self):
        brand = ROOT / "data" / "brands" / "lg"
        web = brand / "web"
        expected = audit_brand(brand)
        actual = load(web / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 81)
        self.assertEqual(actual["errors"]["interpretations"], 105)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 105})
        self.assertEqual(actual["technical_variants"]["entries"], 64)
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 64})

        sources = load(web / "sources.json")
        self.assertEqual(len(sources), 7)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        self.assertTrue({
            "MFL41161610",
            "IM_MultiF_ODU",
            "IM_Multi_F_CeilingCassette",
            "SM_MultiV_5_OutdoorUnits",
            "IM StandardIII Wired Remote PREMTB101",
            "MFL62862020",
            "LG-HVAC-LGMV",
        }.issubset({source["document_ref"] for source in sources}))

        errors = {item["code_display"]: item for item in load(web / "errors" / "index.json")}
        self.assertEqual(errors["CH04"]["interpretation_count"], 2)
        self.assertEqual(errors["CH21"]["interpretation_count"], 2)
        self.assertIn("CH39", errors)
        self.assertIn("CH48", errors)
        ch21 = load(web / "errors" / "details" / f"{errors['CH21']['id']}.json")
        aliases = {item["alias_display"] for item in ch21["aliases"]}
        self.assertTrue({"211", "212", "213"}.issubset(aliases))
        self.assertTrue(all(
            {"cause", "check", "machine_behavior"}.issubset(
                {item["item_type"] for item in interpretation["info_items"]}
            )
            and interpretation["datasets"]
            and interpretation["operational_impacts"]
            and any(source.get("page_start") for source in interpretation["sources"])
            for path in (web / "errors" / "details").glob("*.json")
            for interpretation in load(path)["interpretations"]
        ))

        topics = [load(path) for path in (web / "topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "PREMTB101: historial de hasta 20 errores",
            "CH03: la interior no recibe al mando",
            "Single Zone: Pump Down desde el modo frío",
            "Cassette: CH04 y estado OFF",
            "MULTI V: auto addressing desde SW01C",
            "FDD Fd8/Fd9: todas las unidades a plena carga",
            "Nivel 2: comunicación y recuperación automática",
            "LGMV: monitorización y gráficas",
            "Placa interior: capacidad, EEPROM y grupo",
        }.issubset(titles))
        self.assertTrue(all(
            variant["steps"]
            and variant["sections"]
            and variant["media"] == []
            and any(source.get("page_start") for source in variant["sources"])
            for variant in variants
        ))

        search = load(web / "search.json")
        for query in (
            "CH03",
            "CH04 boya",
            "212",
            "pump down",
            "mando 3 hilos",
            "auto addressing SW01C",
            "Fd8 plena carga",
            "LGMV graficas",
            "CH39 MICOM",
            "CH48 liquida",
        ):
            with self.subTest(query=query):
                self.assertTrue(contains_query(search, query))

        public_text = "\n".join(path.read_text(encoding="utf-8") for path in brand.rglob("*.json"))
        self.assertNotIn("lg-manuals", public_text)
        self.assertFalse(any(brand.rglob("*.pdf")))
        self.assertFalse(any(brand.rglob("*.db")))
        self.assertFalse(any(brand.rglob("*.sqlite")))

    def test_haier_reference_v1_quality_traceability_and_code_layers(self):
        brand = ROOT / "data" / "brands" / "haier"
        web = brand / "web"
        expected = audit_brand(brand)
        actual = load(web / "quality.json")
        self.assertEqual(actual, expected)
        self.assertEqual(actual["errors"]["entries"], 120)
        self.assertEqual(actual["errors"]["interpretations"], 133)
        self.assertEqual(actual["errors"]["status_counts"], {"complete": 133})
        self.assertEqual(actual["technical_variants"]["entries"], 67)
        self.assertEqual(actual["technical_variants"]["status_counts"], {"complete": 67})

        sources = load(web / "sources.json")
        self.assertEqual(len(sources), 8)
        self.assertTrue(all(source["status"] == "reviewed" for source in sources))
        self.assertTrue({
            "HAIER-ADVANCED-PLUS-SM",
            "HAIER-ARCTIC-MULTI-SG-20210508",
            "HAIER-GE-MULTI-SM-20220411",
            "HAIER-FLEXFIT-PRO-SM-20210508",
            "HAIER-MRV-S-ODU-SM",
            "HAIER-MRV-S-COMPACT-CASSETTE-SM",
            "HAIER-YR-E17-CONTROLLER",
            "49-5000680-REV0",
        }.issubset({source["document_ref"] for source in sources}))

        errors = {item["code_display"]: item for item in load(web / "errors" / "index.json")}
        self.assertEqual(errors["0C"]["interpretation_count"], 2)
        self.assertEqual(errors["20"]["interpretation_count"], 3)
        for code in ("E7", "15", "29", "1D"):
            detail = load(web / "errors" / "details" / f"{errors[code]['id']}.json")
            contexts = [
                row
                for interpretation in detail["interpretations"]
                for row in interpretation["indication_contexts"]
            ]
            self.assertTrue(any(row.get("related_error_id") for row in contexts), code)

        code_78 = load(web / "errors" / "details" / f"{errors['78']['id']}.json")
        self.assertIn(
            "no detiene",
            code_78["interpretations"][0]["operational_impacts"][0]["summary"].lower(),
        )
        code_1d = load(web / "errors" / "details" / f"{errors['1D']['id']}.json")
        self.assertTrue(any(
            row["code_display"] == "29"
            for row in code_1d["interpretations"][0]["indication_contexts"]
        ))

        topics = [load(path) for path in (web / "topics").glob("*.json")]
        variants = [variant for topic in topics for variant in topic["variants"]]
        titles = {variant["title"] for variant in variants}
        self.assertTrue({
            "YR-E17: error actual e histórico de todo el grupo",
            "YR-E16B: menú Error Code",
            "MRV: decimal 29 en exterior y hexadecimal 1D en mando",
            "Frío/seco con compresor en marcha",
            "Calor, ventilación o espera",
            "FlexFit Multi: autocomprobación automática CC",
            "MRV: condiciones previas al Trial Operation",
            "Elegir la curva correcta: 10K, 23K o 50K",
            "Código 78: alarma sin parada",
        }.issubset(titles))
        self.assertTrue(all(
            variant["steps"]
            and variant["sections"]
            and variant["media"] == []
            and any(source.get("page_start") for source in variant["sources"])
            for variant in variants
        ))

        public_text = "\n".join(path.read_text(encoding="utf-8") for path in brand.rglob("*.json"))
        self.assertNotIn("tmp\\pdfs\\haier", public_text)
        self.assertNotIn("tmp/text/haier", public_text)
        self.assertFalse(any(brand.rglob("*.pdf")))
        self.assertFalse(any(brand.rglob("*.db")))
        self.assertFalse(any(brand.rglob("*.sqlite")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
