"""
Economic Impact of War - Interactive Dashboard (animated, multi-chart version)
Run with:  streamlit run app.py
Put these 3 files in the SAME folder: app.py, cleaned_data.csv, recovery_rates.csv
Requires: pandas numpy plotly streamlit
"""

import math
import urllib.parse

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Economic Impact of War", page_icon="📉", layout="wide")

NAVY = "#25211C"
FONT = "Inter, Segoe UI, Arial, sans-serif"
ORDER = ["Iraq", "Kuwait", "Rwanda", "Ukraine"]
ISO3 = {"Iraq": "IRQ", "Rwanda": "RWA", "Kuwait": "KWT", "Ukraine": "UKR"}
COLORS = {"Iraq": "#C65D4A", "Kuwait": "#4E7D5B", "Rwanda": "#4F7CAC", "Ukraine": "#D9A441"}
PERIOD_COLORS = {"pre-war": "#8A9A8E", "during-war": "#C65D4A", "post-war": "#4E7D5B"}
BAD, GOOD = "#C65D4A", "#4E7D5B"
IDX_LABEL = "GDP index (100 = last pre-war year)"

# ---------- decorative artwork (look only, carries no data) ----------
def _wave(period, amp, base, phase, fill, crest):
    """One seamless liquid wave layer (2400 wide so it can scroll by half and loop)."""
    pts = [(x, base + amp * math.sin(2 * math.pi * x / period + phase)
            + 0.4 * amp * math.sin(2 * math.pi * x / (period / 2) + phase * 1.7)) for x in range(0, 2401, 20)]
    line = " ".join(f"{x},{y:.1f}" for x, y in pts)
    return (f"<svg class='wv' viewBox='0 0 2400 90' preserveAspectRatio='none' xmlns='http://www.w3.org/2000/svg'>"
            f"<path d='M0,90 L{line} L2400,90 Z' fill='{fill}'/>"
            f"<path d='M{line}' fill='none' stroke='{crest}' stroke-width='1.4' vector-effect='non-scaling-stroke'/></svg>")


HERO_FX = (
    "<i class='lq lq1'></i><i class='lq lq2'></i><i class='lq lq3'></i><i class='lq lq4'></i>"
    "<div class='pane'></div>"
    "<i class='sphere sp1'></i><i class='sphere sp2'></i><i class='sphere sp3'></i>"
    "<div class='waves'>"
    + _wave(1200, 7, 40, 0.0, "rgba(255,255,255,0.10)", "rgba(255,255,255,0.35)")
    .replace("class='wv'", "class='wv w1'")
    + _wave(600, 6, 52, 1.9, "rgba(220,238,214,0.14)", "rgba(255,255,255,0.45)").replace("class='wv'", "class='wv w2'")
    + _wave(400, 5, 66, 3.4, "rgba(255,255,255,0.20)", "rgba(255,255,255,0.65)").replace("class='wv'", "class='wv w3'")
    + "</div><div class='grain'></div>"
)

_PATH = "M10,92 C50,90 85,94 115,98 C140,102 150,170 175,200 C192,150 218,118 252,96 C292,72 342,56 410,30"
HERO_ART = (
    "<svg class='hero-art' viewBox='0 0 420 240' xmlns='http://www.w3.org/2000/svg'>"
    "<g stroke='rgba(255,255,255,0.10)'><line x1='0' y1='50' x2='420' y2='50'/><line x1='0' y1='140' x2='420' y2='140'/>"
    "<line x1='0' y1='215' x2='420' y2='215'/></g>"
    "<line x1='0' y1='95' x2='420' y2='95' stroke='rgba(205,225,190,0.5)' stroke-dasharray='4 6'/>"
    f"<path class='draw' pathLength='100' d='{_PATH}' fill='none' stroke='#C9DDB8' stroke-width='2.4' "
    "stroke-linecap='round' stroke-linejoin='round'/>"
    "<circle class='halo' cx='410' cy='30' r='5' fill='none' stroke='#C9DDB8' stroke-width='1.5'/>"
    "<circle class='endp' cx='410' cy='30' r='4' fill='#FFFFFF'/></svg>"
)

# ---------- realistic animated world map for the hero (decoration only; hand-built coastlines) ----------
_LAND = {}

_LAND["north_america"] = [
(-168,65.6),(-166,68.3),(-162,70.2),(-156.6,71.3),(-152,70.8),(-148,70.3),(-141,69.7),(-136,69),(-132,69.6),(-128,70.1),
(-124,69.4),(-120,69.4),(-116,68),(-113,67.9),(-108,68),(-104,68),(-100,67.8),(-96,68),(-94.8,71.6),(-92,70.3),(-90,68.8),
(-87,68),(-86,66.6),(-88.5,64.8),(-90.7,63.2),(-93.5,61.4),(-94.6,59.2),(-92.8,57.3),(-90,57.2),(-87.5,56.4),(-85,55.2),
(-82.4,53),(-80.6,51.6),(-79.2,53.6),(-78.7,56),(-77.6,58.4),(-78.2,60.6),(-77,62.3),(-73.5,62),(-70,61),(-69,59),(-67.5,58.4),
(-64.5,60.3),(-62,57.6),(-60,55.6),(-57,53.6),(-55.7,52),(-57.5,50.5),(-60.5,50.2),(-64,50.2),(-66.5,50.2),(-68.5,49.2),
(-70.5,47.8),(-69,48.4),(-66.5,49.2),(-64.5,49.2),(-64.3,48.4),(-65.8,47.6),(-64.8,46.3),(-62.2,46),(-61,45.8),(-61.2,45),
(-63.5,44.5),(-65.7,43.6),(-66.8,44.6),(-68.8,44.2),(-70.4,43.3),(-70.2,42),(-71.2,41.5),(-73.7,40.7),(-74,39.6),(-75.4,38.4),
(-76.1,37),(-75.6,35.3),(-77.1,34.6),(-78.9,33.7),(-80.8,32.1),(-81.4,30.6),(-80.5,28.5),(-80.1,26.3),(-80.4,25.3),(-81.2,25.2),
(-82.1,26.6),(-82.8,28.1),(-83.6,29.7),(-85.2,29.7),(-86.6,30.4),(-88.5,30.3),(-89.6,30.2),(-89.3,29),(-90.7,29.1),(-92.2,29.6),
(-93.9,29.7),(-95.1,29),(-96.8,28.1),(-97.4,26.5),(-97.7,24.5),(-97.8,22.5),(-97.2,20.6),(-96.2,19.2),(-95,18.6),(-93.8,18.3),
(-92.4,18.6),(-91,18.8),(-90.5,20.9),(-89,21.5),(-87.2,21.5),(-87.6,19.6),(-88.1,18),(-88.4,16.1),(-87,15.8),(-85,15.9),
(-83.5,15.2),(-83.4,13.2),(-83.7,11.3),(-82.6,9.6),(-81.3,8.9),(-79.8,9.3),(-78.4,9.4),(-77.4,8.7),(-78,8),(-79.2,7.4),
(-80.4,7.3),(-81.6,8.1),(-83,8.3),(-85.5,9.8),(-85.7,11.1),(-87.5,13),(-89.5,13.5),(-91.5,14),(-94,16),(-96,15.7),(-98,16.2),
(-101,17.3),(-103.5,18.6),(-105.5,20),(-105.6,22.6),(-106.6,23.6),(-108,25.5),(-110.6,27.6),(-112.5,29.6),(-114.7,31.7),
(-114.6,30.3),(-113.2,28.4),(-112.2,26.6),(-110.4,24.4),(-109.5,23.2),(-110.4,23.8),(-112.3,25.3),(-114.2,27.6),(-115.2,29.4),
(-116.6,31.5),(-117.2,32.6),(-118.5,34),(-120.6,34.6),(-121.9,36.6),(-122.5,37.8),(-123.8,39.5),(-124.4,40.4),(-124.1,42),
(-124.5,43.6),(-124,46.2),(-124.7,48.4),(-125.6,49.3),(-127.5,50.8),(-129.8,53.2),(-131.5,55),(-133.6,57),(-136,58.2),(-138.5,59.5),
(-141,60),(-144,60.1),(-147.5,60.8),(-150.5,59.6),(-152,59.1),(-153.2,58.4),(-156,57),(-158.5,56.2),(-162,55),(-164.6,54.6),
(-160.5,56.2),(-157.7,58.6),(-158,59.8),(-162,59.9),(-164.5,60.6),(-165.5,62.4),(-164.5,63.2),(-161,64.5),(-163.6,64.6),
(-166,64.6),
]
_LAND["greenland"] = [
(-60,82),(-45,83.2),(-30,83.5),(-19,81.8),(-18.5,79.5),(-20,76.5),(-19.5,74.5),(-22,72.3),(-24,70.2),(-27,68.3),(-32,67.3),
(-38,65.6),(-40.5,64.2),(-42.5,61.5),(-44,59.9),(-47,60.5),(-49.5,62),(-51.5,64.2),(-53,66.5),(-54.2,68.8),(-55.5,70.5),
(-56,72.5),(-58.5,75),(-64,76.5),(-70,77.5),(-72,78.6),(-67,80),
]
_LAND["baffin"] = [(-90,73.3),(-82,73.7),(-76,73),(-71,71.2),(-67,69.2),(-62,66.8),(-64.5,64),(-65,62.3),(-69,62),(-72.5,63.5),
(-74,65.8),(-78,65.2),(-80,63.7),(-83,64.5),(-85,66.8),(-88,69),(-90,70.5)]
_LAND["victoria"] = [(-119,71.5),(-114,73),(-107,73),(-104,72),(-106,70),(-110,68.8),(-115,69),(-118,70)]
_LAND["ellesmere"] = [(-92,76.5),(-85,76.2),(-78,76.5),(-74,78),(-66,80),(-62,82.4),(-72,83),(-85,82.2),(-92,80.5),(-95,78.5)]
_LAND["newfoundland"] = [(-59.4,47.7),(-56,47.4),(-52.7,46.9),(-52.8,48.5),(-55.3,49.9),(-56,51.5),(-57.5,50.5),(-58.5,48.6)]
_LAND["cuba"] = [(-84.9,21.9),(-83,22.9),(-80.5,23.1),(-77.5,21.9),(-74.2,20.2),(-77.2,19.9),(-79.5,21.5),(-81.8,22.2)]
_LAND["hispaniola"] = [(-74.4,18.4),(-72,19.9),(-69.9,19.6),(-68.4,18.6),(-71,17.9),(-73.5,18.1)]
_LAND["iceland"] = [(-24,65.5),(-22,66.4),(-16,66.5),(-13.6,65),(-18,63.4),(-22.5,63.8)]
_LAND["south_america"] = [
(-77.4,8.7),(-76,9.4),(-75.5,10.7),(-74,11.2),(-72.5,11.8),(-71.4,12.3),(-70,12.2),(-68,10.5),(-66,10.7),(-64,10.5),(-62,10.7),
(-61,9),(-60,8.4),(-58,6.8),(-55,5.8),(-52,5),(-51.5,4),(-50.5,1.5),(-50,0),(-48.5,-1),(-45,-1.8),(-42,-2.8),(-39,-3.3),
(-37,-4.9),(-35.2,-5.5),(-34.8,-7.5),(-35.5,-9.5),(-37.5,-12),(-38.5,-13),(-39,-15.5),(-39.2,-18),(-40,-20),(-41,-22),(-43,-23),
(-45,-23.6),(-48,-26),(-48.6,-28.5),(-49,-29.3),(-51,-31),(-52.5,-33),(-54,-34.8),(-56,-34.9),(-57.5,-34.4),(-58.5,-34.3),
(-57,-36.2),(-57.5,-38),(-62,-39),(-62.2,-40.7),(-65,-41),(-64,-42.5),(-65.5,-45),(-67.5,-46.5),(-66,-48),(-68.5,-50.2),
(-69,-52),(-68.4,-53.5),(-66,-55),(-68.5,-55.2),(-71,-54.8),(-74,-52.5),(-75.5,-49),(-74,-45),(-73.7,-42),(-73.5,-39),
(-71.7,-35.5),(-71.5,-33),(-71.5,-30),(-70.3,-26),(-70.2,-22),(-70.2,-18.3),(-72,-17),(-75,-15.5),(-76.5,-13.5),(-77.5,-11),
(-78.5,-8.5),(-79.8,-7),(-81.2,-5.5),(-81,-4),(-80,-2.5),(-80.5,-1),(-80,0.5),(-79,1.8),(-78.5,2.5),(-77.5,4),(-77.3,6),
(-77.6,7.5),
]
_LAND["africa"] = [
(-5.9,35.8),(-2,35.1),(1,36.5),(3,36.8),(8,37),(10.2,37.3),(11,37),(10.5,36),(10.3,34.7),(11,33.5),(13,32.9),(15,32.4),
(18,30.4),(19.5,30.3),(20.1,32),(22,32.9),(24,32.2),(25,31.6),(29,30.9),(31,31.5),(32.3,31.2),(32.6,29.9),(33.7,27.5),
(34.2,26),(35.6,23.8),(37.2,21),(37.5,18.5),(38.5,16.5),(39.5,15.5),(41.5,13.5),(43.2,12.5),(43.3,11.6),(44,10.4),(45,10.4),
(47,11.2),(49,11.5),(51.2,11.8),(51,10.4),(50.2,8.2),(48.5,5.2),(46,2.5),(43.5,0.2),(41.5,-1.8),(40.2,-2.8),(39.2,-4.7),
(38.8,-6.8),(39.5,-8.5),(40.5,-10.5),(40.4,-13),(40.5,-15),(37,-17.8),(35.2,-20),(35.4,-23),(33,-25.5),(32.9,-26.8),
(32.8,-28.5),(31.5,-29.5),(30.2,-31.2),(28,-32.9),(26,-34),(23.5,-34),(20.2,-34.8),(18.5,-34.2),(18.3,-32.6),(17.3,-30.5),
(16.5,-28.6),(15.2,-26.5),(14.5,-23),(12.2,-18.5),(11.8,-16),(13.7,-12),(12.2,-6),(9.5,-1.5),(9.5,1),(9.8,3.9),(8.5,4.5),
(6,4.3),(4.5,6.2),(2,6.3),(-1,5),(-2.8,4.8),(-5,5.2),(-7.5,4.4),(-9,5.2),(-11.5,7),(-13.2,8.5),(-14.5,10.8),(-16.5,12.4),
(-17,14.7),(-16.5,16),(-16.3,19),(-17,21),(-16,23.7),(-14.7,26),(-13.2,27.7),(-10,29.5),(-9.7,31),(-8.5,33.2),(-6.8,34),
]
_LAND["madagascar"] = [(49.3,-12),(50.4,-15.5),(49.5,-17.5),(48.5,-20),(47.3,-24.8),(45,-25.5),(43.7,-23.5),(43.3,-21.5),(44.3,-19.5),(44,-17),(46,-15.8),(48,-13.5)]
_LAND["eurasia"] = [
(-5.4,36.1),(-6.3,36.6),(-7.4,37.2),(-8.9,37),(-9.5,38.7),(-8.8,40.3),(-8.9,42),(-9.3,43),(-8,43.7),(-5.5,43.6),(-3,43.4),
(-1.7,43.4),(-1.3,44.5),(-1.2,46),(-2.5,47.2),(-4.3,47.8),(-4.7,48.4),(-3,48.8),(-1.5,48.7),(-1.4,49.7),(0.2,49.4),(1.5,50.3),
(3,51),(4.3,51.8),(4.8,53),(7,53.5),(8.5,54),(8.7,55.5),(8.2,57),(10.6,57.7),(10.4,56.5),(9.6,55.2),(10.5,54.4),(12,54.2),
(14,54),(16.5,54.5),(19,54.4),(21,55.3),(21,57),(22.5,57.7),(24,57.2),(24.4,58.4),(23.5,59.2),(26,59.6),(28,59.5),(30.2,59.9),
(28.5,60.5),(25,60.3),(22.8,59.9),(21.5,61),(21.4,62.7),(23.5,64.5),(25.4,65.1),(23.5,65.8),(21.5,64.7),(19.5,63.6),(17.5,62.2),
(17.2,60.8),(18.8,59.8),(18.2,59.2),(16.5,57.2),(16,56.2),(14.5,56),(13,55.3),(12.6,56.2),(11.8,57.7),(10.8,59.2),(9.5,58.9),
(8,58.1),(5.8,58.7),(5.2,60.5),(5.5,62),(7.5,63.2),(10.5,64.3),(12.5,66),(14.5,67.8),(16.5,69),(19,70),(23,71),(25.8,71.1),
(30.5,70.2),(33,69.4),(36,69.1),(41.5,67),(41,66.3),(37.5,64.6),(40,64.5),(44,66),(44.5,68.3),(53,68.8),(60,69),(67,68.8),
(68,71),(70,73),(72.5,72.8),(73,68.5),(73.5,66.5),(75,68),(78,72),(80,73.3),(87,74.5),(98,76.2),(104,77.7),(112,76.5),
(113,73.8),(120,73),(128,72),(131,71),(140,72.5),(150,71.5),(160,70),(170,70),(176,69.7),(180,68.9),(186,67.6),(190,66),
(189.5,64.8),(187,64.3),(180,64.7),(177,62.5),(170,60),(164,59.8),(162,57.8),(163,56.2),(163,54.5),(160,52.8),(156.7,51),
(156,52.5),(155.5,56),(156,57.5),(158,58),(160,60.5),(155,59.2),(150,59.5),(143,59.3),(138,56.2),(137,54),(141,53.2),
(141.5,52),(140.3,48.5),(139,47),(135.5,43.5),(132,43),(130,42.5),(129.5,41),(128,39.5),(127.5,38.5),(129.4,36.5),(129.2,35.1),
(127,34.5),(126.3,35),(126.6,37.2),(125,37.7),(125.3,39.5),(124.4,40),(122,40.5),(121.5,39),(121,40.8),(122.2,40.4),(120,39.8),
(118,39.1),(117.8,38.2),(119,37.2),(122.5,37.4),(121,36.5),(119.5,35),(120.8,33),(121.8,31.5),(121.9,30),(121.5,28.5),
(120.5,27),(119.5,25.5),(117.5,23.8),(115,22.7),(113.5,22.2),(111,21.5),(110.3,20.2),(108.3,21.7),(106.7,20),(105.8,18.8),
(107.5,16.5),(108.8,14.2),(109.3,12),(108.8,11),(107,10.4),(105,8.7),(104.8,10),(103.5,10.5),(102.8,12),(100.5,13.4),
(100,12.5),(99.2,10),(100.3,8),(101.3,6.8),(102.5,6),(103.5,5),(103.5,2.5),(104.2,1.4),(103.5,1.4),(101.8,2.8),(100.5,4.3),
(100.2,6.5),(98.4,8),(98.3,10),(98.7,12),(97.7,16.5),(94.4,16),(94.2,18.3),(92.3,20.5),(91.8,22.6),(90.5,22),(89,21.7),
(87,21.5),(86.5,20),(84.8,19),(82.3,16.5),(80.2,15.3),(80.2,13),(79.8,10.5),(79.2,9.2),(78,8.8),(77.5,8.1),(76.3,9.8),
(75.3,11.8),(74.2,14.8),(73.2,17.5),(72.8,19.1),(72.6,21),(72.2,21.8),(70.5,20.8),(69,22.3),(68.3,23.6),(67,24.6),(65.5,25.2),
(62.3,25.2),(60.5,25.3),(58,25.6),(57,27),(56.3,27.2),(54,26.7),(51.5,27.8),(50,30),(48.8,30.2),(48,29.4),(48.5,28),(50,26.5),
(50.2,25.2),(51.2,24.5),(51.6,25.7),(52.5,24.2),(54.5,24.3),(56,25.6),(56.4,26.2),(56.8,24.5),(58.5,23.6),(59.8,22.4),
(58.8,20.5),(57.5,18.8),(55.5,17.2),(52.5,16.2),(50,15.8),(48,14),(45,12.8),(43.4,12.7),(42.8,14.5),(42.5,16.5),(41,19),
(39.2,21.5),(38.5,23.5),(37,25.8),(35.5,28),(34.9,29.5),(34.4,28),(33.9,27.2),(33.5,28.4),(32.6,29.9),(32.3,31.2),(34.2,31.3),
(34.9,32.6),(35.5,33.9),(35.8,35.5),(36.2,36.7),(35,36.6),(34,36.2),(32.5,36.1),(30.5,36.6),(29,36.6),(27.5,37),(27.2,37.9),
(26.5,39.5),(26.2,40.1),(26.5,40.6),(24.5,40.9),(23.7,40.2),(22.9,40.5),(23.1,39.5),(22.8,38.8),(24,38),(23,36.5),(22.2,36.6),
(21.7,36.8),(21.5,37.8),(21.2,38.5),(20.8,39.6),(19.4,40.2),(19.5,41.7),(18.5,42.5),(16.5,43.5),(15,44.5),(13.7,45.2),
(13.7,45.7),(12.3,45.3),(12.4,44.2),(13.5,43.6),(14.3,42.3),(16,41.9),(17,40.8),(18.5,40.1),(17,39.5),(16.5,38.9),(15.7,38),
(15.9,38.7),(15.6,40),(14.3,40.7),(13,41.2),(11.2,42.4),(10.2,43.9),(8.8,44.4),(7.5,43.8),(6,43.1),(4.3,43.4),(3.1,42.9),
(3.2,41.9),(2.1,41.3),(0.8,40.8),(0,39.6),(-0.3,38.8),(-0.7,37.6),(-2,36.8),(-4.4,36.7),
]
_LAND["britain"] = [(-5.7,50),(-3,50.6),(-0.5,50.8),(0.9,50.9),(1.4,51.3),(1.7,52.7),(0.4,53.2),(-0.1,53.6),(-0.5,54.5),(-1.4,55.4),
(-2.1,56),(-2.4,56.5),(-1.8,57.5),(-3.5,57.7),(-4,58.6),(-3,58.6),(-5,58.6),(-5.8,57.6),(-5.6,56.5),(-6,55.5),(-5.2,55),
(-4.8,54.8),(-3.5,54.9),(-3,54),(-3.1,53.3),(-4.5,53.3),(-4.2,52.5),(-5.2,51.8),(-3,51.4),(-4.5,51.2)]
_LAND["ireland"] = [(-6.1,52.2),(-6.0,53.4),(-5.5,54.6),(-6.3,55.2),(-7.6,55.3),(-8.6,54.6),(-10.1,54.2),(-9.9,52.2),(-9.6,51.5),(-8,51.6),(-6.4,52.2)]
_LAND["sicily"] = [(12.4,37.8),(13.5,38.2),(15.6,38.3),(15.1,37),(15,36.7),(12.6,37.6)]
_LAND["sardinia"] = [(8.2,41.0),(9.7,41.2),(9.7,39.2),(8.5,39),(8.4,40.3)]
_LAND["corsica"] = [(8.6,42.4),(9.4,43),(9.5,41.5),(8.8,41.6)]
_LAND["crete"] = [(23.5,35.4),(26.3,35.3),(26,35),(24,35.1)]
_LAND["cyprus"] = [(32.3,35),(34.5,35.6),(34,34.9),(32.6,34.6)]
_LAND["svalbard"] = [(11,78.5),(14,79.8),(20,80.3),(26,79.6),(22,77.5),(16,76.8)]
_LAND["novaya_zemlya"] = [(51.5,71.5),(55,73.5),(58,75),(68,77),(60,75),(57,73),(55,71),(52,70.5)]
_LAND["honshu"] = [(130.9,34),(132.5,35.5),(135.2,35.7),(136.7,37.3),(139.2,38),(140,40.5),(141.5,41.2),(141.9,39.5),(141,37.5),
(140.8,35.7),(139.8,35),(138,34.7),(136.8,34.4),(135.1,33.6),(134.4,34.2),(132.5,34)]
_LAND["hokkaido"] = [(140,41.5),(141.2,43.2),(142,45.5),(144.5,44),(145.5,43.3),(143.2,42),(141,42.5),(140.3,41.8)]
_LAND["kyushu"] = [(129.8,33.2),(131,34),(132,33.2),(131.4,31.4),(130.2,31.3),(129.6,32.5)]
_LAND["shikoku"] = [(132.5,33.8),(134.5,34.2),(134.4,33.3),(133,32.8)]
_LAND["sakhalin"] = [(142,54.3),(143.5,53),(143.2,50),(144.5,49),(143.5,46.5),(142,46),(142.2,49),(141.7,51.5),(142,53)]
_LAND["taiwan"] = [(121,25.1),(122,24.9),(121,22),(120.1,23),(120.7,24.6)]
_LAND["hainan"] = [(108.6,19.6),(110.5,20),(111,19.2),(109.5,18.2),(108.7,18.5)]
_LAND["sri_lanka"] = [(79.8,9.8),(81.8,7.5),(81.2,6.2),(80,6),(79.7,7.5)]
_LAND["luzon"] = [(120.4,18.5),(122.2,18.5),(122,16.3),(121.5,14.3),(123.8,13.1),(122.5,13.6),(120.8,14.2),(120.3,16)]
_LAND["mindanao"] = [(122,7),(123.5,8.5),(126.2,9.3),(126.5,7),(125.5,5.8),(124,6.5),(122.2,6.9)]
_LAND["visayas"] = [(122,10.5),(123.6,11.2),(125.2,11.3),(125.4,9.9),(123.2,9.3)]
_LAND["borneo"] = [(109,1.5),(111,1.8),(113,3.2),(115,5),(117,7),(119,5.3),(118,4.2),(117.8,1.5),(116.5,-1.5),(116,-3.8),
(114.5,-4),(112.5,-3.4),(110.5,-3),(110,-1.2),(109,0)]
_LAND["sumatra"] = [(95.3,5.6),(97.5,5.2),(100,2.5),(103,0.5),(104.5,-1.5),(106,-3.5),(105.8,-5.8),(104.5,-5.8),(102,-4),
(100.5,-1.5),(98.8,1.8),(96.5,3.8)]
_LAND["java"] = [(105.2,-6.8),(106.5,-6),(108.5,-6.6),(111,-6.5),(112.8,-7.2),(114.5,-7.8),(114.4,-8.7),(111,-8.2),(108,-7.8),(106,-7.3)]
_LAND["sulawesi"] = [(119.6,-5.5),(119.4,-3),(120,-1),(120.2,0.7),(121.5,1.2),(124.8,1.4),(123.5,0.2),(121.8,0.4),(121.2,-1),
(123.3,-0.9),(122.3,-3),(123.2,-4.5),(122,-4.8),(121,-3),(120.5,-5.5)]
_LAND["new_guinea"] = [(131,-0.8),(134,-0.8),(135.5,-3.3),(138,-1.7),(141,-2.6),(144.5,-3.8),(145.8,-5.5),(147.5,-6.2),(147.7,-8),
(150.3,-10.4),(147,-10),(144.5,-7.8),(143.2,-9),(141,-9.1),(139,-8),(138,-8.3),(137.8,-5.5),(135,-4.3),(133,-4),(132.5,-2.8),(131.4,-1.9)]
_LAND["australia"] = [(113.3,-22),(114.1,-26),(115,-30),(115,-33.5),(116,-35),(118,-35),(120,-34),(123.5,-34),(126,-32.3),
(129,-31.6),(131.3,-31.5),(134,-32.7),(135.8,-34.8),(137.5,-33),(138,-35),(139.7,-37.5),(141,-38.2),(144,-38.4),(146.4,-39),
(148,-37.8),(150,-37),(151,-34),(153,-31),(153.6,-28.5),(153,-25.7),(150.8,-22.5),(149,-20.5),(146.3,-19),(145.4,-16),
(145.2,-14.5),(143.5,-14),(142.5,-10.7),(141.6,-12.5),(141.5,-15),(140,-17.7),(137.8,-16.5),(136,-15.2),(136.8,-12.2),
(133,-11.5),(131.2,-12),(130,-13),(128,-14.9),(126.8,-14),(125,-15.5),(123.5,-17),(122,-18),(121,-19.5),(118.5,-20.3),
(116,-21),(114.5,-21.7)]
_LAND["tasmania"] = [(145.2,-40.8),(148.3,-40.9),(148,-43),(146.2,-43.6),(145.2,-42)]
_LAND["nz_north"] = [(172.7,-34.4),(174.5,-35.8),(176,-37.5),(178.5,-37.7),(177.5,-39.3),(176.8,-40),(175.2,-41.6),(174.8,-40),
(173.9,-39.2),(174.8,-37.3),(174.2,-36.2)]
_LAND["nz_south"] = [(172.8,-40.5),(174,-41.6),(173.1,-43.2),(171.2,-44.5),(170.5,-46),(168.5,-46.6),(166.5,-46),(167.5,-44.5),
(169,-43.5),(171,-42),(172.5,-40.5)]

# seas / lakes cut out of the land (even-odd)
_HOLES = {
"black_sea": [(28,41.9),(29.2,41.2),(31,41.1),(33,41.9),(35.5,42),(36,41.4),(38,41),(40,41),(41.5,41.5),(41.6,42.6),(40,43.5),
(38.5,44.4),(37.3,44.8),(36.6,45.3),(35.4,44.9),(34.3,44.5),(33.6,44.4),(32.5,45.4),(33.6,46.1),(32,46.5),(31,46.6),(30.3,46.2),
(29.7,45.2),(28.8,44.4),(28.5,43.4),(27.8,42.5)],
"azov": [(35.2,45.3),(35.5,46),(37.5,47),(39,47.1),(38.5,46.2),(37,45.3),(36.6,45.3)],
"caspian": [(46.8,44.4),(47.5,45.7),(49.2,46.4),(51.5,46.8),(53.2,46.6),(53,45.3),(51.2,44.6),(50.3,44.6),(50.3,43.2),(51.3,43),
(52.7,42),(53,41.2),(52.9,40.2),(53.9,39.2),(53,39.3),(53.9,37.3),(52,36.7),(50.2,37),(49,37.6),(48.9,38.5),(49.4,40.2),
(49.8,40.5),(48.5,41.8),(47.5,43)],
"superior": [(-92,46.8),(-89,48),(-86,48.7),(-84.6,47),(-87,46.5),(-90,46.6)],
"michigan": [(-87.8,42.2),(-87,45.5),(-85,45.8),(-86,43.5)],
"huron": [(-84,46),(-82,46),(-80.2,44.8),(-81.7,43.3),(-83.4,44),(-83.5,45.5)],
"erie": [(-83.4,41.7),(-81,41.5),(-79,42.8),(-81,42.6),(-83,42)],
"ontario": [(-79.8,43.3),(-76.5,43.6),(-76.2,44.1),(-79,43.9)],
}

_CTRY = {
"Iraq": [(42.4,37.1),(44.2,37.0),(44.8,37.2),(45.5,36),(45.7,35),(46.1,33.9),(47.6,32.9),(48,31.5),(47.7,30.9),(48,30),
(47.2,30),(46.5,29.1),(44.7,29.2),(41.9,31.2),(39.2,32.1),(38.8,33.4),(41,34.4),(41.4,35.6)],
"Kuwait": [(46.6,28.9),(47.7,28.5),(48.4,28.5),(48.2,29.2),(47.7,30.1),(47,29.9),(46.6,29.1)],
"Rwanda": [(28.9,-2.4),(29.3,-2.8),(30.5,-2.4),(30.9,-1.5),(30.4,-1.1),(29.6,-1.4),(29,-1.7)],
"Ukraine": [(22.1,48.4),(22.8,47.9),(24.5,47.9),(26.6,48.3),(27.5,48.4),(29.2,47.5),(28.2,46.5),(28.3,45.5),(29.6,45.3),
(30.7,46.5),(32,46.4),(33.6,46.1),(32.5,45.3),(33.6,44.4),(35.4,44.9),(36.5,45.3),(35.6,46.3),(37.5,47.1),(38.1,47.1),
(39.8,48.5),(40.1,49.6),(38,49.9),(35.5,50.4),(34.3,51.3),(32.5,52.2),(30.5,51.4),(28,51.6),(26,51.9),(24.1,51.6),(23.5,50.4),(22.5,49.1)],
}
_HOT = {"Iraq": (43.7, 33.0), "Kuwait": (47.6, 29.3), "Rwanda": (29.9, -1.95), "Ukraine": (31.3, 49.0)}
_CITIES = [(-74,40.7),(-118.2,34),(-87.6,41.9),(-99.1,19.4),(-79.4,43.7),(-95.4,29.8),(-80.2,25.8),(-74.1,4.7),(-77,-12),
(-46.6,-23.5),(-43.2,-22.9),(-58.4,-34.6),(-70.6,-33.4),(-0.1,51.5),(2.35,48.9),(-3.7,40.4),(13.4,52.5),(12.5,41.9),(37.6,55.8),
(29,41),(31.2,30),(3.4,6.5),(36.8,-1.3),(28,-26.2),(18.4,-33.9),(38.7,9),(15.3,-4.3),(46.7,24.7),(51.4,35.7),(55.3,25.2),
(67,24.9),(72.9,19.1),(77.2,28.6),(90.4,23.8),(100.5,13.8),(106.8,-6.2),(103.8,1.35),(114.2,22.3),(116.4,39.9),(121.5,31.2),
(127,37.6),(139.7,35.7),(121,14.6),(151.2,-33.9),(145,-37.8),(115.9,-32),(83,55),(30.5,50.4),(44.4,33.3),(47.98,29.37),(30.06,-1.95)]


_LON0, _LON1, _LAT0, _LAT1 = -170.0, 190.0, -58.0, 83.0
_MW = 1000.0
_PXR = _MW / math.radians(_LON1 - _LON0)


def _mil(lat):
    p = math.radians(max(_LAT0, min(_LAT1, lat)))
    return 1.25 * math.log(math.tan(math.pi / 4 + 0.4 * p))


_YT, _YB = _mil(_LAT1), _mil(_LAT0)
_MH = (_YT - _YB) * _PXR


def _mproj(lon, lat):
    return ((lon - _LON0) / (_LON1 - _LON0) * _MW, (_YT - _mil(lat)) * _PXR)


def _smooth(pts, closed=True):
    n = len(pts)
    if n < 4:
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    out = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return "".join(out) + ("Z" if closed else "")


def _poly(coords):
    return _smooth([_mproj(lon, lat) for lon, lat in coords])


def _arc(a, b, lift=0.32):
    (x1, y1), (x2, y2) = a, b
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    d = math.hypot(x2 - x1, y2 - y1)
    return f"M{x1:.1f},{y1:.1f} Q{mx:.1f},{my - d * lift:.1f} {x2:.1f},{y2:.1f}"


@st.cache_data(show_spinner=False)
def _build_hero_map():
    land_d = "".join(_poly(v) for v in _LAND.values()) + "".join(_poly(v) for v in _HOLES.values())
    hp = {k: _mproj(*v) for k, v in _HOT.items()}

    grat = ""
    for lon in range(-150, 190, 30):
        x = _mproj(lon, 0)[0]
        grat += f"<line x1='{x:.1f}' y1='0' x2='{x:.1f}' y2='{_MH:.0f}'/>"
    for lat in range(-30, 90, 30):
        y = _mproj(0, lat)[1]
        grat += f"<line x1='0' y1='{y:.1f}' x2='{_MW:.0f}' y2='{y:.1f}'/>"
    eq = _mproj(0, 0)[1]

    base = (
        f"<svg class='hm hm-base' viewBox='0 0 {_MW:.0f} {_MH:.0f}' preserveAspectRatio='xMidYMid meet' xmlns='http://www.w3.org/2000/svg'>"
        "<defs>"
        f"<path id='hmLand' fill-rule='evenodd' d='{land_d}'/>"
        "<clipPath id='hmClip' clip-rule='evenodd'><use href='#hmLand'/></clipPath>"
        "<linearGradient id='hmGrad' x1='0' y1='0' x2='0.4' y2='1'><stop offset='0' stop-color='#DDD7C0'/><stop offset='0.55' stop-color='#C8C9AC'/><stop offset='1' stop-color='#B6BC9A'/></linearGradient>"
        "<linearGradient id='hmRose' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#D4607C'/><stop offset='1' stop-color='#8F2B49'/></linearGradient>"
        "<radialGradient id='hmSea' cx='0.5' cy='0.5' r='0.7'><stop offset='0' stop-color='#FFFFFF' stop-opacity='0.30'/><stop offset='1' stop-color='#F3D9D6' stop-opacity='0.10'/></radialGradient>"
        "<filter id='hmFx' x='-2%' y='-2%' width='104%' height='104%' color-interpolation-filters='sRGB'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.045' numOctaves='3' seed='11' result='nz'/>"
        "<feDisplacementMap in='SourceGraphic' in2='nz' scale='4.5' xChannelSelector='R' yChannelSelector='G' result='rough'/>"
        "<feGaussianBlur in='rough' stdDeviation='1.5' result='soft'/>"
        "<feDiffuseLighting in='soft' surfaceScale='2.4' diffuseConstant='1.15' lighting-color='#FFFDF4' result='edge'><feDistantLight azimuth='235' elevation='58'/></feDiffuseLighting>"
        "<feComposite in='edge' in2='rough' operator='in' result='edgeIn'/>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.016 0.022' numOctaves='5' seed='7' result='mt'/>"
        "<feDiffuseLighting in='mt' surfaceScale='7' diffuseConstant='1' lighting-color='#FFFFFF' result='terr'><feDistantLight azimuth='235' elevation='48'/></feDiffuseLighting>"
        "<feComponentTransfer in='terr' result='terrSoft'><feFuncR type='linear' slope='0.22' intercept='0.78'/><feFuncG type='linear' slope='0.22' intercept='0.78'/><feFuncB type='linear' slope='0.22' intercept='0.78'/></feComponentTransfer>"
        "<feComposite in='terrSoft' in2='rough' operator='in' result='terrIn'/>"
        "<feColorMatrix in='mt' type='matrix' values='0 0 0 0 0.52  0 0 0 0 0.47  0 0 0 0 0.33  1.0 0 0 0 -0.40' result='mot'/>"
        "<feComposite in='mot' in2='rough' operator='in' result='motIn'/>"
        "<feBlend in='rough' in2='terrIn' mode='multiply' result='a'/>"
        "<feBlend in='a' in2='edgeIn' mode='multiply' result='b'/>"
        "<feMerge><feMergeNode in='b'/><feMergeNode in='motIn'/></feMerge></filter>"
        "<filter id='hmBlur' x='-5%' y='-5%' width='110%' height='110%'><feGaussianBlur stdDeviation='4'/></filter>"
        "<filter id='hmBlur2' x='-5%' y='-5%' width='110%' height='110%'><feGaussianBlur stdDeviation='2.4'/></filter>"
        "</defs>"
        f"<rect width='{_MW:.0f}' height='{_MH:.0f}' fill='url(#hmSea)'/>"
        f"<g stroke='rgba(70,50,30,0.10)' stroke-width='0.8' fill='none'>{grat}</g>"
        f"<line x1='0' y1='{eq:.1f}' x2='{_MW:.0f}' y2='{eq:.1f}' stroke='rgba(70,50,30,0.22)' stroke-width='0.9' stroke-dasharray='3 5'/>"
        "<use href='#hmLand' fill='none' stroke='rgba(255,255,255,0.75)' stroke-width='9' filter='url(#hmBlur)' opacity='0.55'/>"
        "<use href='#hmLand' x='2' y='4' fill='rgba(60,40,20,0.34)' filter='url(#hmBlur2)'/>"
        "<g filter='url(#hmFx)'><use href='#hmLand' fill='url(#hmGrad)'/></g>"
        "<g clip-path='url(#hmClip)'>"
        + "".join(f"<path d='{_poly(v)}' fill='url(#hmRose)' opacity='0.86' stroke='rgba(255,255,255,0.7)' stroke-width='0.8'/>"
                  for v in _CTRY.values())
        + "</g>"
        "<use href='#hmLand' fill='none' stroke='rgba(255,255,255,0.7)' stroke-width='0.8'/>"
        "</svg>"
    )

    clouds = (
        f"<svg class='hm hm-clouds' viewBox='0 0 {_MW:.0f} {_MH:.0f}' preserveAspectRatio='xMidYMid meet' xmlns='http://www.w3.org/2000/svg'>"
        "<defs><filter id='hmCl' x='0' y='0' width='100%' height='100%' color-interpolation-filters='sRGB'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.0055 0.011' numOctaves='5' seed='21' stitchTiles='stitch'/>"
        "<feColorMatrix type='matrix' values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 2.6 -1.18'/></filter></defs>"
        f"<g class='hm-cl'><rect width='{_MW:.0f}' height='{_MH:.0f}' filter='url(#hmCl)'/>"
        f"<rect x='{_MW:.0f}' width='{_MW:.0f}' height='{_MH:.0f}' filter='url(#hmCl)'/></g></svg>"
    )

    live = [
        f"<svg class='hm hm-live' viewBox='0 0 {_MW:.0f} {_MH:.0f}' preserveAspectRatio='xMidYMid meet' xmlns='http://www.w3.org/2000/svg'>",
        "<defs>"
        "<radialGradient id='hmHot'><stop offset='0' stop-color='#FFFFFF'/><stop offset='0.35' stop-color='#FF7C9C'/><stop offset='1' stop-color='#E0456E' stop-opacity='0'/></radialGradient>"
        "<linearGradient id='hmScan' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#fff' stop-opacity='0'/><stop offset='0.5' stop-color='#fff' stop-opacity='0.42'/><stop offset='1' stop-color='#fff' stop-opacity='0'/></linearGradient>"
        "<filter id='hmGlow' x='-100%' y='-100%' width='300%' height='300%'><feGaussianBlur stdDeviation='2.2'/></filter>"
        "</defs>",
        f"<rect class='hm-scan' x='-160' y='0' width='160' height='{_MH:.0f}' fill='url(#hmScan)'/>",
    ]
    cities = ""
    for i, (lo, la) in enumerate(_CITIES):
        x, y = _mproj(lo, la)
        cities += (f"<g class='hm-city' style='animation-delay:{(i * 0.37) % 5:.1f}s'>"
                   f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.4' fill='#FFC978' opacity='0.35' filter='url(#hmGlow)'/>"
                   f"<circle cx='{x:.1f}' cy='{y:.1f}' r='1.1' fill='#FFF3D6'/></g>")
    live.append(cities)

    nyc, bei, syd, sao, mum, tok = (_mproj(-74, 40.7), _mproj(116.4, 39.9), _mproj(151.2, -33.9),
                                    _mproj(-46.6, -23.5), _mproj(72.9, 19.1), _mproj(139.7, 35.7))
    arcs = [
        (hp["Ukraine"], nyc, 0.30, 7.0), (hp["Ukraine"], bei, 0.26, 8.2), (hp["Iraq"], tok, 0.28, 9.0),
        (hp["Kuwait"], syd, 0.28, 8.0), (hp["Rwanda"], sao, 0.30, 7.4), (hp["Rwanda"], mum, 0.32, 6.4),
        (hp["Ukraine"], hp["Iraq"], 0.45, 4.6), (hp["Iraq"], hp["Rwanda"], 0.34, 5.6),
        (hp["Kuwait"], hp["Rwanda"], 0.36, 5.2), (hp["Ukraine"], hp["Kuwait"], 0.42, 5.0),
    ]
    for i, (a, b, lift, dur) in enumerate(arcs):
        d = _arc(a, b, lift)
        live.append(
            f"<path d='{d}' fill='none' stroke='rgba(190,60,95,0.55)' stroke-width='1.3'/>"
            f"<path class='hm-flow' style='animation-duration:{dur + 3:.1f}s' d='{d}' fill='none' stroke='#FFF0F3' stroke-width='1.7' "
            "stroke-linecap='round' stroke-dasharray='2 12' opacity='0.9'/>"
            f"<circle r='2.4' fill='#FFFFFF'><animateMotion dur='{dur}s' begin='-{(i * 1.3) % dur:.1f}s' repeatCount='indefinite' path='{d}'/></circle>"
            f"<circle r='6' fill='#FF8FA8' opacity='0.35' filter='url(#hmGlow)'><animateMotion dur='{dur}s' begin='-{(i * 1.3) % dur:.1f}s' repeatCount='indefinite' path='{d}'/></circle>"
        )

    label_off = {"Iraq": (-12, -9, "end"), "Kuwait": (11, 13, "start"), "Rwanda": (11, 4, "start"), "Ukraine": (-11, -8, "end")}
    for i, (name, (x, y)) in enumerate(hp.items()):
        dx, dy, anchor = label_off[name]
        live.append(
            f"<g class='hm-hot' style='animation-delay:{i * 0.7:.1f}s'>"
            f"<circle class='hm-ring' cx='{x:.1f}' cy='{y:.1f}' r='14' fill='none' stroke='#E0456E' stroke-width='1.4'/>"
            f"<circle class='hm-ring r2' cx='{x:.1f}' cy='{y:.1f}' r='14' fill='none' stroke='#E0456E' stroke-width='1.1'/>"
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='15' fill='url(#hmHot)' opacity='0.9'/>"
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='3.2' fill='#FFFFFF' stroke='#E0456E' stroke-width='1.2'/></g>"
            f"<text class='hm-lbl' x='{x + dx:.1f}' y='{y + dy:.1f}' text-anchor='{anchor}'>{name}</text>"
        )
    live.append("</svg>")
    return "<div class='hero-map'>" + base + clouds + "".join(live) + "</div>"


HERO_ART = _build_hero_map()

BRAND = (
    "<div class='brand'><div class='bm'><svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>"
    "<polyline points='3,8 8,10 12,18 16,11 21,5' fill='none' stroke='#C9DDB8' stroke-width='2' "
    "stroke-linecap='round' stroke-linejoin='round'/></svg></div>"
    "<div><div class='bt'>Economic Impact of War</div><div class='bs'>Iraq · Kuwait · Rwanda · Ukraine</div></div></div>"
)

SCENE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 340 300'>
<defs>
<linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#1C2B22' stop-opacity='0'/><stop offset='0.32' stop-color='#1C2B22' stop-opacity='0.9'/><stop offset='0.68' stop-color='#6F8A74'/><stop offset='1' stop-color='#E6CDA0'/></linearGradient>
<linearGradient id='haze' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#EAD3AE' stop-opacity='0'/><stop offset='1' stop-color='#EAD3AE' stop-opacity='0.34'/></linearGradient>
<filter id='bl' x='-50%' y='-50%' width='200%' height='200%'><feGaussianBlur stdDeviation='5'/></filter>
<filter id='bs' x='-50%' y='-50%' width='200%' height='200%'><feGaussianBlur stdDeviation='1.4'/></filter>
</defs>
<style>
.sun{animation:br 12s ease-in-out infinite}
@keyframes br{0%,100%{opacity:.7}50%{opacity:1}}
.pl{transform-box:fill-box;transform-origin:center bottom;animation:pl 14s ease-out infinite}
@keyframes pl{0%{transform:translateY(0) scale(.7);opacity:0}25%{opacity:.6}100%{transform:translateY(-60px) scale(1.8);opacity:0}}
.tank{animation:roll 70s linear infinite}
@keyframes roll{from{transform:translateX(-130px)}to{transform:translateX(380px)}}
</style>
<rect width='340' height='300' fill='url(#sky)'/>
<circle class='sun' cx='238' cy='214' r='70' fill='#F2B98A' opacity='.3' filter='url(#bl)'/>
<circle cx='238' cy='214' r='19' fill='#F6D2A4' opacity='.92' filter='url(#bs)'/>
<path fill='#6B8470' opacity='.62' d='M0 270 V196 H22 V182 H40 V200 H58 V170 H70 L75 164 L80 172 H98 V196 H116 V186 H136 V206 H154 V180 H176 V200 H196 V188 H214 V210 H236 V184 H258 V204 H280 V176 H300 V198 H322 V190 H340 V270 Z'/>
<rect y='170' width='340' height='100' fill='url(#haze)'/>
<path fill='#2A3B2F' opacity='.95' d='M0 276 V224 H16 V208 L24 202 L33 211 V230 H52 V198 H60 V190 H78 V218 H94 V236 H114 V212 H124 L131 205 V232 H150 V276 Z'/>
<path fill='#2A3B2F' opacity='.95' d='M196 276 V236 H214 V210 H234 V202 L243 211 V230 H262 V216 H284 V240 H302 V220 H318 V204 L330 198 V236 H340 V276 Z'/>
<g fill='#17241C' filter='url(#bl)' opacity='.55'><ellipse class='pl' cx='71' cy='190' rx='9' ry='7'/><ellipse class='pl' style='animation-delay:5s' cx='71' cy='190' rx='9' ry='7'/><ellipse class='pl' style='animation-delay:9s' cx='71' cy='190' rx='9' ry='7'/><ellipse class='pl' style='animation-delay:2s' cx='238' cy='198' rx='9' ry='7'/><ellipse class='pl' style='animation-delay:7s' cx='238' cy='198' rx='9' ry='7'/></g>
<path fill='#101B15' d='M0 280 L24 274 L52 279 L84 272 L120 278 L158 273 L198 279 L238 272 L276 278 L312 273 L340 278 V300 H0 Z'/>
<g transform='translate(0,251) scale(.82)'><g class='tank' fill='#0B130E'>
<rect x='0' y='23' width='84' height='12' rx='6'/>
<polygon points='2,24 16,12 70,12 84,24'/>
<path d='M24 12 Q26 1 38 1 L54 1 Q60 4 60 12 Z'/>
<rect x='58' y='4.4' width='44' height='3.2'/><rect x='99' y='3.4' width='6' height='5.2'/>
<g fill='#25352A'><circle cx='10' cy='29' r='4'/><circle cx='24' cy='29' r='4'/><circle cx='41' cy='29' r='4'/><circle cx='58' cy='29' r='4'/><circle cx='73' cy='29' r='4'/></g>
</g></g>
<g stroke='#08100B' stroke-width='1.3' fill='none'><path d='M0 292 L340 292'/>__POSTS__</g>
</svg>""".replace("__POSTS__", "".join(f"<line x1='{x}' y1='282' x2='{x}' y2='300'/>" for x in range(24, 340, 80)))
SCENE_URI = "data:image/svg+xml;utf8," + urllib.parse.quote(SCENE_SVG)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

:root {
  --ink: #0F1B3D; --muted: #5A6785; --line: #E3E8F4; --card: #FFFFFF;
  --indigo: #5E7A62; --teal: #0E9F8E; --soft: #F1F4FC;
}

/* ---------- animated page background ---------- */
.stApp {
  background: linear-gradient(135deg, #F7F9FF, #EDF2FD, #F4F9FB, #EEF3EA, #F7F9FF);
  background-size: 400% 400%; animation: pagebg 26s ease infinite;
  font-family: 'Inter', 'Segoe UI', sans-serif; color: var(--ink);
}
.stApp::before {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(520px 420px at 8% 12%, rgba(59,76,202,0.10), transparent 70%),
    radial-gradient(460px 380px at 92% 22%, rgba(14,159,142,0.10), transparent 70%),
    radial-gradient(500px 420px at 70% 96%, rgba(214,69,93,0.07), transparent 70%);
  animation: drift 22s ease-in-out infinite alternate;
}
.block-container {position: relative; z-index: 1; padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1280px;}
#MainMenu, footer {visibility: hidden;}
h1, h2, h3, h4, .stTabs [data-baseweb="tab"] {font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif !important;}
h3 {border-left: 5px solid var(--indigo); padding-left: 12px !important; letter-spacing: -0.2px;}
h4 {color: var(--ink); letter-spacing: -0.1px;}
p, label, .stMarkdown, .stCaption {font-family: 'Inter', 'Segoe UI', sans-serif;}

/* ---------- animated hero ---------- */
.hero {position: relative; overflow: hidden; padding: 36px 42px; border-radius: 22px; margin-bottom: 20px;
       background:
         radial-gradient(rgba(255,255,255,0.10) 1px, transparent 1px) 0 0 / 22px 22px,
         linear-gradient(120deg, #0F1B3D, #1F3A93, #5E7A62, #12807A, #1F3A93, #0F1B3D);
       background-size: 22px 22px, 320% 320%; animation: flow 18s ease infinite;
       box-shadow: 0 18px 40px rgba(30,42,34,0.22), 0 2px 6px rgba(30,42,34,0.12);}
.hero::before {content: ""; position: absolute; width: 280px; height: 280px; right: -70px; top: -110px;
               border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,0.20), rgba(255,255,255,0.02) 70%);
               animation: float 8s ease-in-out infinite;}
.hero::after {content: ""; position: absolute; width: 170px; height: 170px; right: 200px; bottom: -80px;
              border-radius: 50%; background: radial-gradient(circle, rgba(242,163,58,0.45), rgba(242,163,58,0) 70%);
              animation: float 10s ease-in-out infinite reverse;}
.hero .sweep {position: absolute; top: 0; bottom: 0; width: 38%; left: -45%; z-index: 1; pointer-events: none;
              background: linear-gradient(100deg, transparent, rgba(255,255,255,0.13), transparent);
              transform: skewX(-18deg); animation: sweep 7s ease-in-out infinite;}
.hero .orb {position: absolute; border-radius: 50%; z-index: 1; pointer-events: none;}
.hero .o1 {width: 12px; height: 12px; right: 18%; top: 28%; background: rgba(255,255,255,0.65);
           box-shadow: 0 0 0 0 rgba(255,255,255,0.5); animation: pulse 3.2s ease-out infinite;}
.hero .o2 {width: 9px; height: 9px; right: 9%; top: 62%; background: #F2A33A;
           box-shadow: 0 0 0 0 rgba(242,163,58,0.55); animation: pulse 3.8s ease-out infinite 1s;}
.hero .o3 {width: 8px; height: 8px; right: 30%; top: 70%; background: #5EEAD4;
           box-shadow: 0 0 0 0 rgba(94,234,212,0.5); animation: pulse 4.4s ease-out infinite 2s;}
.hero h1 {color: #FFFFFF; margin: 0; padding: 0; font-size: 2.5rem; font-weight: 800; letter-spacing: -0.6px;
          animation: slidein 0.9s ease both; position: relative; z-index: 2;}
.hero p {color: #D6E2FF; margin: 10px 0 16px 0; font-size: 1.05rem; position: relative; z-index: 2;
         max-width: 760px; line-height: 1.55; animation: slidein 1.2s ease both;}
.chips {position: relative; z-index: 2; animation: slidein 1.5s ease both;}
.chips span {display: inline-block; background: rgba(255,255,255,0.14); color: #FFFFFF; font-size: 0.82rem;
             padding: 6px 15px; border-radius: 999px; margin: 0 8px 6px 0; backdrop-filter: blur(6px);
             border: 1px solid rgba(255,255,255,0.22); transition: background .25s, transform .25s;}
.chips span:hover {background: rgba(255,255,255,0.26); transform: translateY(-2px);}

@keyframes pagebg {0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;}}
@keyframes drift {from {transform: translate3d(0,0,0) scale(1);} to {transform: translate3d(2%, 3%, 0) scale(1.06);}}
@keyframes flow {0% {background-position: 0 0, 0% 50%;} 50% {background-position: 0 0, 100% 50%;} 100% {background-position: 0 0, 0% 50%;}}
@keyframes float {0%, 100% {transform: translateY(0);} 50% {transform: translateY(20px);}}
@keyframes sweep {0% {left: -45%;} 55%, 100% {left: 125%;}}
@keyframes pulse {0% {box-shadow: 0 0 0 0 rgba(255,255,255,0.55);} 70%, 100% {box-shadow: 0 0 0 16px rgba(255,255,255,0);}}
@keyframes slidein {from {opacity: 0; transform: translateX(-30px);} to {opacity: 1; transform: none;}}
@keyframes fadeup {from {opacity: 0; transform: translateY(18px);} to {opacity: 1; transform: none;}}
@keyframes shimmer {from {transform: translateX(-100%);} to {transform: translateX(100%);}}
@keyframes barline {from {transform: scaleX(0);} to {transform: scaleX(1);}}

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] {gap: 6px; background: var(--card); padding: 6px; border-radius: 16px;
                                   border: 1px solid var(--line); box-shadow: 0 4px 16px rgba(30,42,34,0.06);
                                   overflow-x: auto;}
.stTabs [data-baseweb="tab"] {font-weight: 600; padding: 10px 16px; border-radius: 11px; color: var(--muted);
                              background: transparent; transition: background .25s, color .25s, transform .25s;}
.stTabs [data-baseweb="tab"]:hover {background: var(--soft); color: var(--indigo); transform: translateY(-1px);}
.stTabs [data-baseweb="tab"][aria-selected="true"] {color: #FFFFFF;
      background: linear-gradient(120deg, #5E7A62, #2F6FE0); box-shadow: 0 6px 16px rgba(59,76,202,0.32);}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display: none;}
.stTabs [data-baseweb="tab-panel"] {animation: fadeup 0.55s ease both; padding-top: 18px;}

/* ---------- chart cards ---------- */
[data-testid="stPlotlyChart"] {background: var(--card); border-radius: 18px; padding: 8px 8px 2px 8px;
        border: 1px solid var(--line); box-shadow: 0 4px 18px rgba(30,42,34,0.07);
        transition: box-shadow .3s, transform .3s, border-color .3s;}
[data-testid="stPlotlyChart"]:hover {box-shadow: 0 14px 34px rgba(30,42,34,0.14); transform: translateY(-3px);
        border-color: rgba(80,60,40,0.22);}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {background: linear-gradient(180deg, #F8FAFF 0%, #E9EEFC 100%);
        border-right: 1px solid var(--line);}
section[data-testid="stSidebar"]::before {content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px; z-index: 5;
        background: linear-gradient(90deg, #5E7A62, #0E9F8E, #F2A33A, #5E7A62); background-size: 300% 100%;
        animation: pagebg 8s linear infinite;}
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h1 {font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: var(--ink); letter-spacing: -0.2px;}
section[data-testid="stSidebar"] [data-testid="stExpander"] {background: var(--card); border-radius: 14px;
        border: 1px solid var(--line); box-shadow: 0 2px 10px rgba(30,42,34,0.05);}

/* ---------- widgets ---------- */
span[data-baseweb="tag"] {background: linear-gradient(120deg, #5E7A62, #2F6FE0) !important; color: #FFFFFF !important;
        border-radius: 8px !important;}
div[data-baseweb="select"] > div {border-radius: 12px !important; border-color: var(--line) !important;
        transition: box-shadow .25s, border-color .25s;}
div[data-baseweb="select"] > div:hover {border-color: var(--indigo) !important; box-shadow: 0 0 0 3px rgba(59,76,202,0.12);}
div[data-baseweb="slider"] div[role="slider"] {background: var(--indigo) !important; box-shadow: 0 0 0 5px rgba(59,76,202,0.16);
        transition: box-shadow .25s;}
div[data-baseweb="slider"] div[role="slider"]:hover {box-shadow: 0 0 0 9px rgba(59,76,202,0.18);}
.stButton > button, .stDownloadButton > button {border-radius: 12px; font-weight: 600; border: 1px solid var(--indigo);
        color: #FFFFFF; background: linear-gradient(120deg, #5E7A62, #2F6FE0); padding: 0.55rem 1.1rem;
        box-shadow: 0 6px 16px rgba(59,76,202,0.28); transition: transform .25s, box-shadow .25s, filter .25s;}
.stButton > button:hover, .stDownloadButton > button:hover {transform: translateY(-2px); filter: brightness(1.06);
        box-shadow: 0 12px 24px rgba(59,76,202,0.36); color: #FFFFFF; border-color: var(--indigo);}
[data-testid="stMetric"] {background: var(--card); border: 1px solid var(--line); border-radius: 16px;
        padding: 12px 16px; box-shadow: 0 3px 14px rgba(30,42,34,0.06); transition: transform .25s, box-shadow .25s;}
[data-testid="stMetric"]:hover {transform: translateY(-3px); box-shadow: 0 10px 24px rgba(30,42,34,0.12);}
[data-testid="stMetricValue"] {font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800; color: var(--ink);}
[data-testid="stDataFrame"] {border-radius: 16px; overflow: hidden; border: 1px solid var(--line);
        box-shadow: 0 4px 18px rgba(30,42,34,0.07);}
[data-testid="stAlert"] {border-radius: 14px;}
hr {border-color: var(--line) !important;}

/* ---------- insight box ---------- */
.insight {background: linear-gradient(120deg, #FFFFFF, #F1F5FF); border: 1px solid var(--line);
          border-left: 5px solid var(--indigo); padding: 16px 22px; margin-top: 16px;
          border-radius: 14px; color: var(--ink); line-height: 1.85; box-shadow: 0 4px 16px rgba(30,42,34,0.06);
          animation: slidein 0.8s ease both;}

/* ---------- animated progress bars ---------- */
.pbar {margin: 16px 0; padding: 14px 18px; background: var(--card); border: 1px solid var(--line);
       border-radius: 14px; box-shadow: 0 3px 12px rgba(30,42,34,0.05); transition: transform .25s, box-shadow .25s;}
.pbar:hover {transform: translateX(4px); box-shadow: 0 8px 20px rgba(30,42,34,0.10);}
.plabel {display: flex; justify-content: space-between; color: var(--ink); margin-bottom: 8px; font-size: 0.95rem;}
.ptrack {background: rgba(80,60,40,0.10); border-radius: 999px; height: 16px; overflow: hidden;}
.pfill {position: relative; overflow: hidden; height: 100%; border-radius: 999px;
        animation: grow 1.6s cubic-bezier(.2,.8,.2,1) both;}
.pfill::after {content: ""; position: absolute; inset: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.45), transparent);
        animation: shimmer 2.4s ease-in-out infinite 1.6s;}
@keyframes grow {from {width: 0;}}

/* ---------- accent: burgundy ---------- */
:root {--indigo: #7A1633; --burg: #5A0F26; --gold: #D9B26A;}
h3 {border-left: 4px solid #7A1633; background: none; animation: none; padding-bottom: 0 !important;}
.stTabs [data-baseweb="tab"][aria-selected="true"] {background: linear-gradient(120deg, #5A0F26, #8E1B3A);
      box-shadow: 0 6px 16px rgba(90,15,38,0.30);}
.stTabs [data-baseweb="tab"]:hover {color: #7A1633;}
span[data-baseweb="tag"] {background: linear-gradient(120deg, #5A0F26, #8E1B3A) !important;}
.stButton > button, .stDownloadButton > button {border-color: #5A0F26; background: linear-gradient(120deg, #5A0F26, #8E1B3A);
      box-shadow: 0 6px 16px rgba(90,15,38,0.26);}
.stButton > button:hover, .stDownloadButton > button:hover {border-color: #5A0F26; box-shadow: 0 12px 24px rgba(90,15,38,0.34);}
div[data-baseweb="slider"] div[role="slider"] {background: #7A1633 !important; box-shadow: 0 0 0 5px rgba(122,22,51,0.16);}
div[data-baseweb="select"] > div:hover {border-color: #7A1633 !important; box-shadow: 0 0 0 3px rgba(122,22,51,0.12);}
.insight {border-left-color: #7A1633;}
@keyframes marquee {from {transform: translateX(0);} to {transform: translateX(-50%);}}
@keyframes fadein {to {opacity: 1;}}
@keyframes drawonce {to {stroke-dashoffset: 0;}}
@keyframes halo {0% {transform: scale(1); opacity: .7;} 100% {transform: scale(3.6); opacity: 0;}}
@keyframes ember {0% {transform: translate(0,0); opacity: 0;} 15% {opacity: .8;} 100% {transform: translate(var(--dx), -190px); opacity: 0;}}
@keyframes topo {from {transform: translateX(0);} to {transform: translateX(-24px);}}

/* ---------- hero: burgundy briefing banner ---------- */
.hero {padding: 46px 48px 42px; min-height: 0; border-radius: 16px; border: 1px solid rgba(217,178,106,0.30);
       background: radial-gradient(700px 320px at 88% 0%, rgba(190,60,90,0.28), transparent 70%),
                   linear-gradient(135deg, #2D0817 0%, #470E26 55%, #5A1531 100%);
       background-size: auto; animation: none;
       box-shadow: 0 18px 40px rgba(60,10,28,0.32), 0 2px 6px rgba(45,8,23,0.30);}
.hero::before {content: ""; position: absolute; left: 16px; top: 16px; right: auto; bottom: auto; width: 22px; height: 22px;
               border: 0; border-top: 1px solid rgba(217,178,106,0.6); border-left: 1px solid rgba(217,178,106,0.6);
               border-radius: 0; background: none; animation: none; z-index: 2;}
.hero::after {content: ""; position: absolute; right: 16px; bottom: 16px; left: auto; top: auto; width: 22px; height: 22px;
              border: 0; border-bottom: 1px solid rgba(217,178,106,0.6); border-right: 1px solid rgba(217,178,106,0.6);
              border-radius: 0; background: none; animation: none; z-index: 2;}
.hero h1 {font-family: 'Fraunces', Georgia, serif !important; font-weight: 600; font-size: 2.7rem; letter-spacing: -0.01em;
          line-height: 1.1; color: #FFFFFF;}
.hero .rule {width: 56px; height: 2px; background: #D9B26A; margin: 16px 0 14px; position: relative; z-index: 2;
             animation: slidein 1.1s ease both;}
.hero p {color: #EBCFD6; max-width: 54%; font-size: 1.02rem; margin: 0 0 18px 0;}
.hero .chips span {background: transparent; border: 1px solid rgba(217,178,106,0.38); color: #F3DDE2; font-size: .78rem;
                   padding: 4px 12px; border-radius: 4px; backdrop-filter: none; letter-spacing: .2px;}
.hero .chips span:hover {background: rgba(217,178,106,0.12); transform: none;}
.hero-topo {position: absolute; inset: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none;}
.hero-topo .tp {animation: topo 50s ease-in-out infinite alternate;}
.hero .grain {position: absolute; inset: 0; z-index: 1; pointer-events: none; opacity: .10; mix-blend-mode: overlay;
              background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");}
.ember {position: absolute; left: var(--x); bottom: -6px; width: var(--s); height: var(--s); border-radius: 50%; z-index: 1;
        pointer-events: none; background: #FFC48A; box-shadow: 0 0 5px 1px rgba(255,150,70,0.7); opacity: 0;
        animation: ember var(--dur) ease-out infinite var(--del);}
.hero-art {position: absolute; right: 36px; top: 50%; transform: translateY(-50%); width: 36%; max-width: 440px;
           z-index: 1; pointer-events: none; opacity: .92; filter: none;}
.hero-art .draw {stroke-dasharray: 100; stroke-dashoffset: 100; animation: drawonce 3.6s cubic-bezier(.4,0,.2,1) .4s forwards;}
.hero-art .endp {opacity: 0; animation: fadein .5s ease 3.9s forwards;}
.hero-art .halo {opacity: 0; transform-box: fill-box; transform-origin: center; animation: halo 2.8s ease-out 4.2s infinite;}
@media (max-width: 900px) {.hero {padding: 34px 24px 32px;} .hero h1 {font-size: 2.1rem;} .hero p {max-width: 100%;}
                           .hero-art {display: none;}}

/* ---------- ticker ---------- */
.ticker {overflow: hidden; border-radius: 10px; padding: 11px 0; margin: 2px 0 14px;
         background: linear-gradient(120deg, #2D0817, #4A1028); border: 1px solid rgba(217,178,106,0.25);
         box-shadow: 0 8px 22px rgba(60,10,28,0.22);
         -webkit-mask-image: linear-gradient(90deg, transparent, #000 5%, #000 95%, transparent);
         mask-image: linear-gradient(90deg, transparent, #000 5%, #000 95%, transparent);}
.tk-track {display: inline-flex; white-space: nowrap; animation: marquee 38s linear infinite;}
.ticker:hover .tk-track {animation-play-state: paused;}
.tk {color: #EBCFD6; font-size: .85rem; padding: 0 28px; border-right: 1px solid rgba(217,178,106,0.22);}
.tk b {margin-right: 9px; letter-spacing: .6px; filter: brightness(1.5);}
.tk i {font-style: normal; color: #C9A3AE; margin-right: 9px;}
.tk em {font-style: normal; font-weight: 700; color: #FF9AA8; margin-right: 10px;}
.tk span {color: #C9DDB8;}

/* ---------- sidebar: brand + war-theme scene ---------- */
section[data-testid="stSidebar"]::before {height: 3px; animation: none; background: linear-gradient(90deg, #5A0F26, #D9B26A);
                                           background-size: auto;}
.brand {display: flex; align-items: center; gap: 12px; padding: 12px 14px; margin: 0 0 12px 0; border-radius: 12px;
        background: #FFFFFF; border: 1px solid var(--line); border-left: 4px solid #5A0F26;
        box-shadow: 0 4px 14px rgba(30,42,34,0.07); animation: slidein .9s ease both;}
.brand .bm {width: 40px; height: 40px; flex: none; border-radius: 10px; display: flex; align-items: center; justify-content: center;
            background: linear-gradient(135deg, #3A0B1E, #6B1530);}
.brand .bm svg {width: 24px; height: 24px;}
.brand .bt {font-family: 'Fraunces', Georgia, serif; font-weight: 600; font-size: .98rem; line-height: 1.18; color: var(--ink);}
.brand .bs {font-size: .72rem; color: var(--muted); margin-top: 3px;}
section[data-testid="stSidebar"]::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 300px; z-index: 3; pointer-events: none;
  background: url("__SCENE__") no-repeat bottom center / 100% auto;
}

/* =====================================================================
   LIQUID GLASS LAYER
   ===================================================================== */
@property --n {syntax: '<integer>'; initial-value: 0; inherits: false;}
:root {
  --g-bg: linear-gradient(115deg, rgba(255,255,255,0.58) 0%, rgba(255,255,255,0.15) 30%, rgba(255,255,255,0) 54%),
          linear-gradient(135deg, rgba(255,255,255,0.50), rgba(255,255,255,0.20));
  --g-brd: 1px solid rgba(255,255,255,0.78);
  --g-blur: blur(20px) saturate(175%);
  --g-shadow: 0 14px 42px rgba(80,12,44,0.15), 0 2px 6px rgba(80,12,44,0.06), inset 0 1px 0 rgba(255,255,255,1),
              inset 0 0 26px rgba(255,255,255,0.26), inset 0 -1px 0 rgba(255,255,255,0.35);
}

/* ---- liquid backdrop the glass refracts ---- */
.stApp {background: linear-gradient(135deg, #FBF3F6 0%, #F4EAF3 50%, #F8F0EA 100%); animation: none;}
.stApp::before {content: ""; position: fixed; inset: -25%; z-index: 0; pointer-events: none; filter: blur(34px);
  background: radial-gradient(36% 32% at 18% 24%, rgba(150,30,66,0.46), transparent 70%),
              radial-gradient(32% 28% at 80% 16%, rgba(242,163,58,0.38), transparent 70%),
              radial-gradient(38% 34% at 72% 80%, rgba(59,111,224,0.30), transparent 70%);
  animation: liquid1 30s ease-in-out infinite alternate;}
.stApp::after {content: ""; position: fixed; inset: -25%; z-index: 0; pointer-events: none; filter: blur(40px); opacity: 1;
  background: radial-gradient(30% 28% at 28% 82%, rgba(14,159,142,0.32), transparent 70%),
              radial-gradient(28% 26% at 92% 52%, rgba(214,69,93,0.34), transparent 70%),
              radial-gradient(26% 24% at 52% 8%, rgba(190,120,200,0.26), transparent 70%);
  background-size: auto; background-position: 0 0; animation: liquid2 38s ease-in-out infinite alternate;}
@keyframes liquid1 {0% {transform: translate3d(-3%, -2%, 0) rotate(0deg) scale(1);}
                    100% {transform: translate3d(4%, 3%, 0) rotate(14deg) scale(1.12);}}
@keyframes liquid2 {0% {transform: translate3d(3%, 2%, 0) rotate(0deg) scale(1.08);}
                    100% {transform: translate3d(-4%, -3%, 0) rotate(-16deg) scale(1);}}
@keyframes gkin {from {opacity: 0; transform: translateY(24px) scale(.97);} to {opacity: 1; transform: none;}}
@keyframes gkglow {from {transform: translate(-6%, -4%) scale(1);} to {transform: translate(8%, 6%) scale(1.2);}}
@keyframes cnt {from {--n: 0;} to {--n: var(--to);}}
@keyframes sheen {0% {transform: translateX(-70%);} 100% {transform: translateX(70%);}}
@keyframes morph {0% {border-radius: 42% 58% 63% 37% / 45% 38% 62% 55%;}
                  50% {border-radius: 63% 37% 45% 55% / 38% 60% 40% 62%;}
                  100% {border-radius: 38% 62% 55% 45% / 58% 42% 58% 42%;}}
@keyframes roam {0% {transform: translate(0,0) rotate(0deg) scale(1);} 100% {transform: translate(60px, 24px) rotate(40deg) scale(1.18);}}
@keyframes bobs {0%, 100% {transform: translateY(0);} 50% {transform: translateY(-14px);}}
@keyframes wvl {from {transform: translateX(0);} to {transform: translateX(-50%);}}
@keyframes wvr {from {transform: translateX(-50%);} to {transform: translateX(0);}}

/* ---- glass surfaces ---- */
[data-testid="stPlotlyChart"], .insight, .pbar, [data-testid="stMetric"], .brand,
.stTabs [data-baseweb="tab-list"], section[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stDataFrame"] {
  background: var(--g-bg) !important; border: var(--g-brd) !important; box-shadow: var(--g-shadow) !important;
  -webkit-backdrop-filter: var(--g-blur); backdrop-filter: var(--g-blur);}
[data-testid="stPlotlyChart"] {position: relative; overflow: hidden; border-radius: 22px; padding: 10px 10px 2px 10px;}
[data-testid="stPlotlyChart"]::after, .gk::after {content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 5;
  background: linear-gradient(115deg, transparent 38%, rgba(255,255,255,0.55) 50%, transparent 62%);
  transform: translateX(-130%); transition: transform 1s cubic-bezier(.2,.7,.2,1);}
[data-testid="stPlotlyChart"]:hover::after, .gk:hover::after {transform: translateX(130%);}
[data-testid="stPlotlyChart"]:hover {transform: translateY(-3px); border-color: rgba(255,255,255,0.95) !important;
  box-shadow: 0 18px 44px rgba(80,12,44,0.18), inset 0 1px 0 #fff, inset 0 -1px 0 rgba(255,255,255,0.35) !important;}
.insight {border-radius: 20px; border-left: 1px solid rgba(255,255,255,0.78) !important; position: relative;}
.insight::before {content: ""; position: absolute; left: 0; top: 14px; bottom: 14px; width: 4px; border-radius: 4px;
  background: linear-gradient(180deg, #7A1633, #D6455D);}
.pbar {border-radius: 18px;}
.ptrack {background: rgba(90,15,38,0.10); box-shadow: inset 0 1px 3px rgba(60,10,28,0.15);}
.pfill {box-shadow: 0 0 12px rgba(255,255,255,0.45) inset, 0 2px 10px rgba(60,10,28,0.20);}
[data-testid="stMetric"] {border-radius: 18px;}
[data-testid="stDataFrame"] {border-radius: 18px; overflow: hidden;}

/* ---- tabs ---- */
.stTabs [data-baseweb="tab-list"] {border-radius: 18px;}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, rgba(110,20,48,0.94), rgba(170,40,74,0.86)); border: 1px solid rgba(255,255,255,0.35);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.50), 0 8px 22px rgba(90,15,38,0.32);}

/* ---- sidebar ---- */
section[data-testid="stSidebar"] {background: linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,232,240,0.42));
  -webkit-backdrop-filter: blur(24px) saturate(170%); backdrop-filter: blur(24px) saturate(170%);
  border-right: 1px solid rgba(255,255,255,0.75); box-shadow: 6px 0 30px rgba(80,12,44,0.08);}
section[data-testid="stSidebar"] > div {background: transparent !important;}
.brand {border-radius: 16px; border-left: 1px solid rgba(255,255,255,0.78) !important;}
.brand .bm {box-shadow: inset 0 1px 0 rgba(255,255,255,0.4), 0 6px 14px rgba(90,15,38,0.30);}

/* ---- KPI glass cards ---- */
.gk-row {display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 16px; margin: 4px 0 18px;}
.gk {position: relative; overflow: hidden; border-radius: 22px; padding: 18px 22px 18px;
     background: var(--g-bg); border: var(--g-brd); box-shadow: var(--g-shadow);
     -webkit-backdrop-filter: var(--g-blur); backdrop-filter: var(--g-blur);
     animation: gkin .9s cubic-bezier(.2,.8,.2,1) backwards var(--d); transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s;}
.gk > * {position: relative; z-index: 2;}
.gk::before {content: ""; position: absolute; left: -30%; top: -70%; width: 130%; height: 130%; z-index: 1; pointer-events: none;
     background: radial-gradient(circle, var(--c), transparent 66%); opacity: .26; filter: blur(14px);
     animation: gkglow 9s ease-in-out infinite alternate;}
.gk:hover {transform: translateY(-7px); box-shadow: 0 22px 46px rgba(80,12,44,0.20), inset 0 1px 0 #fff, inset 0 -1px 0 rgba(255,255,255,0.35);}
.gk-top {display: flex; align-items: center; gap: 8px; color: var(--c); font-weight: 700; font-size: 13px;
         letter-spacing: .6px; text-transform: uppercase; filter: brightness(.85);}
.gk-dot {width: 9px; height: 9px; border-radius: 50%; background: var(--c); box-shadow: 0 0 0 0 var(--c); animation: ping 2.6s ease-out infinite;}
@keyframes ping {0% {box-shadow: 0 0 0 0 var(--c);} 70%, 100% {box-shadow: 0 0 0 9px transparent;}}
.gk-big {font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif; font-size: 42px; font-weight: 800; color: #1B1230;
         line-height: 1.15; margin-top: 6px; letter-spacing: -1px;}
.count {--n: 0; counter-reset: num var(--n); animation: cnt 1.5s cubic-bezier(.2,.8,.2,1) both var(--d);}
.count::after {content: counter(num);}
.gk-sub {color: #5A4A66; font-size: 13px; margin-top: 2px;}
.gk-badge {display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 600; margin-top: 12px;
           backdrop-filter: blur(6px);}
.gk-badge.ok {background: rgba(14,159,142,0.15); color: #08695d; border: 1px solid rgba(14,159,142,0.32);}
.gk-badge.warn {background: rgba(242,163,58,0.20); color: #8a5a08; border: 1px solid rgba(242,163,58,0.40);}

/* ---- hero: liquid glass over burgundy ---- */
.hero {padding: 48px 52px 78px; border-radius: 26px; border: 1px solid rgba(255,255,255,0.32);
       background: linear-gradient(135deg, #2A0716 0%, #46102A 60%, #5C1633 100%);
       box-shadow: 0 24px 56px rgba(60,10,28,0.34), inset 0 1px 0 rgba(255,255,255,0.40), inset 0 -1px 0 rgba(255,255,255,0.08);}
.hero::before, .hero::after {display: none;}
.hero .lq {position: absolute; z-index: 0; pointer-events: none; filter: blur(30px); opacity: .9;
           animation: morph 15s ease-in-out infinite alternate, roam 24s ease-in-out infinite alternate;}
.hero .lq1 {width: 340px; height: 300px; left: -70px; top: -90px; background: #C2264D;}
.hero .lq2 {width: 300px; height: 260px; right: 8%; bottom: -120px; background: #F2A33A; opacity: .75; animation-duration: 18s, 28s;}
.hero .lq3 {width: 260px; height: 250px; left: 38%; top: -110px; background: #8E1B3A; animation-duration: 13s, 21s;}
.hero .lq4 {width: 220px; height: 200px; right: -50px; top: 20px; background: #E86A8A; opacity: .65; animation-duration: 17s, 26s;}
.hero .pane {position: absolute; inset: 16px; z-index: 1; border-radius: 20px; overflow: hidden; pointer-events: none;
             background: linear-gradient(135deg, rgba(255,255,255,0.16), rgba(255,255,255,0.04));
             border: 1px solid rgba(255,255,255,0.28); -webkit-backdrop-filter: blur(16px) saturate(150%); backdrop-filter: blur(16px) saturate(150%);
             box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), inset 0 0 40px rgba(255,255,255,0.05);}
.hero .pane::after {content: ""; position: absolute; inset: 0;
             background: linear-gradient(115deg, transparent 30%, rgba(255,255,255,0.15) 48%, transparent 62%); animation: sheen 9s ease-in-out infinite alternate;}
.hero .sphere {position: absolute; z-index: 1; border-radius: 50%; pointer-events: none;
   background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.88), rgba(255,255,255,0.20) 26%, rgba(255,255,255,0.05) 58%, rgba(255,190,205,0.24));
   box-shadow: inset -6px -8px 18px rgba(130,20,60,0.35), inset 4px 4px 10px rgba(255,255,255,0.50), 0 16px 30px rgba(20,0,10,0.35);
   animation: bobs 9s ease-in-out infinite;}
.hero .sp1 {width: 58px; height: 58px; right: 5%; top: 14%;}
.hero .sp2 {width: 34px; height: 34px; right: 30%; bottom: 24%; animation-duration: 11s; animation-delay: -3s;}
.hero .sp3 {width: 22px; height: 22px; left: 46%; top: 16%; animation-duration: 8s; animation-delay: -5s;}
.hero .waves {position: absolute; left: 0; right: 0; bottom: 0; height: 74px; z-index: 1; pointer-events: none; overflow: hidden;
              border-radius: 0 0 26px 26px;}
.hero .wv {position: absolute; left: 0; bottom: 0; width: 200%; height: 100%;}
.hero .w1 {animation: wvl 26s linear infinite;}
.hero .w2 {animation: wvr 19s linear infinite; height: 82%;}
.hero .w3 {animation: wvl 14s linear infinite; height: 62%;}
.hero .grain {opacity: .08;}
.hero h1, .hero .rule, .hero p, .hero .chips {position: relative; z-index: 3;}
.hero-art {z-index: 2; right: 56px;}
.hero .chips span {background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.30); border-radius: 10px;
                   -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
                   box-shadow: inset 0 1px 0 rgba(255,255,255,0.35);}
.hero .chips span:hover {background: rgba(255,255,255,0.22);}

/* ---- ticker as dark glass ---- */
.ticker {background: linear-gradient(120deg, rgba(45,8,23,0.72), rgba(92,22,51,0.62)); border: 1px solid rgba(255,255,255,0.22);
         -webkit-backdrop-filter: blur(16px) saturate(150%); backdrop-filter: blur(16px) saturate(150%);
         box-shadow: 0 10px 28px rgba(60,10,28,0.22), inset 0 1px 0 rgba(255,255,255,0.28);}
@media (max-width: 900px) {.hero {padding: 36px 26px 72px;}}

/* ---- liquid backdrop blobs (real shapes that morph) ---- */
div[data-testid="stElementContainer"]:has(.lgbg), div.element-container:has(.lgbg) {position: absolute; width: 0; height: 0; margin: 0;}
div[data-testid="stElementContainer"]:has(iframe[height="0"]), div.element-container:has(iframe[height="0"]) {
  position: absolute; width: 0; height: 0; margin: 0; overflow: hidden;}
.lgbg {position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden;}
.lgbg i {position: absolute; display: block; width: 44vmax; height: 44vmax; filter: blur(80px); opacity: .40; will-change: transform, border-radius;
         animation: morph 22s ease-in-out infinite alternate, roamb 34s ease-in-out infinite alternate;}
.lgbg .b1 {left: -12vmax; top: -10vmax; background: #B92B55;}
.lgbg .b2 {right: -14vmax; top: 4vmax; width: 38vmax; height: 38vmax; background: #F2A33A; animation-duration: 26s, 38s; animation-delay: -8s, -12s;}
.lgbg .b3 {left: 30vw; bottom: -20vmax; background: #3B6FE0; opacity: .28; animation-duration: 30s, 42s; animation-delay: -4s, -20s;}
.lgbg .b4 {right: 6vw; bottom: -14vmax; background: #E86A8A; animation-duration: 24s, 36s; animation-delay: -14s, -6s;}
.lgbg .b5 {left: -8vmax; bottom: 8vmax; width: 30vmax; height: 30vmax; background: #0E9F8E; opacity: .26; animation-duration: 28s, 40s; animation-delay: -10s, -2s;}
@keyframes roamb {0% {transform: translate3d(0,0,0) rotate(0deg) scale(1);} 100% {transform: translate3d(8vw, 6vh, 0) rotate(60deg) scale(1.16);}}
.stApp::before {opacity: .55;} .stApp::after {opacity: .55;}

/* ---- smoother, more liquid motion ---- */
.gk, [data-testid="stPlotlyChart"] {transition: transform .45s cubic-bezier(.2,.8,.2,1), box-shadow .45s, border-radius .8s cubic-bezier(.2,.8,.2,1), border-color .4s;}
.gk:hover {border-radius: 30px 20px 30px 20px;}
[data-testid="stPlotlyChart"]:hover {border-radius: 28px 20px 28px 20px;}
.stTabs [data-baseweb="tab"] {transition: background .4s cubic-bezier(.2,.8,.2,1), color .3s, transform .4s cubic-bezier(.2,.8,.2,1), box-shadow .4s;}
.hero .pane::before {content: ""; position: absolute; left: -12%; right: -12%; top: -70%; height: 110%; border-radius: 50%;
  background: radial-gradient(ellipse at 50% 100%, rgba(255,255,255,0.30), rgba(255,255,255,0.06) 55%, transparent 70%);}
.hero {transition: box-shadow .6s;}
.hero:hover {box-shadow: 0 30px 66px rgba(60,10,28,0.40), inset 0 1px 0 rgba(255,255,255,0.45), inset 0 -1px 0 rgba(255,255,255,0.10);}
.gk-big, .gk-top, .gk-sub {text-shadow: 0 1px 0 rgba(255,255,255,0.55);}

/* =====================================================================
   PALETTE v3 (sage green + forest ink) and iOS-style motion
   ===================================================================== */
:root {--indigo: #5E7A62; --ink: #1E2A22; --muted: #5B685F; --line: #E0E7DC; --ios: cubic-bezier(.32,.72,0,1);
  --g-shadow: 0 14px 40px rgba(30,60,40,0.13), 0 2px 6px rgba(30,60,40,0.05), inset 0 1px 0 rgba(255,255,255,1),
              inset 0 0 26px rgba(255,255,255,0.26), inset 0 -1px 0 rgba(255,255,255,0.35);}
html, body, .stApp {-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;}
.stApp {background: linear-gradient(135deg, #F6F8F3 0%, #EEF2EA 52%, #F7F5EE 100%);}
.stApp::before {opacity: .6; background:
  radial-gradient(36% 32% at 18% 24%, rgba(125,139,113,0.40), transparent 70%),
  radial-gradient(32% 28% at 80% 16%, rgba(226,196,140,0.26), transparent 70%),
  radial-gradient(38% 34% at 72% 80%, rgba(110,170,150,0.26), transparent 70%);}
.stApp::after {opacity: .6; background:
  radial-gradient(30% 28% at 28% 82%, rgba(150,170,120,0.26), transparent 70%),
  radial-gradient(28% 26% at 92% 52%, rgba(150,175,190,0.24), transparent 70%),
  radial-gradient(26% 24% at 52% 8%, rgba(190,205,150,0.24), transparent 70%);}
.lgbg .b1 {background: #8FA484;} .lgbg .b2 {background: #E3C48B; opacity: .30;} .lgbg .b3 {background: #7FB5A0; opacity: .30;}
.lgbg .b4 {background: #A9B88F;} .lgbg .b5 {background: #6E9B86; opacity: .24;}

h3 {border-left-color: #5E7A62;}
.stTabs [data-baseweb="tab"][aria-selected="true"] {background: linear-gradient(135deg, rgba(74,104,80,0.95), rgba(112,143,113,0.90));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.5), 0 8px 22px rgba(74,104,80,0.30);}
.stTabs [data-baseweb="tab"]:hover {color: #5E7A62;}
.stTabs [data-baseweb="tab"][aria-selected="true"]:hover {color: #FFFFFF;}
span[data-baseweb="tag"] {background: linear-gradient(120deg, #4A6850, #6F8F70) !important;}
.stButton > button, .stDownloadButton > button {border-color: #5E7A62; background: linear-gradient(120deg, #4A6850, #6F8F70);
  box-shadow: 0 6px 16px rgba(74,104,80,0.26); transition: transform .5s var(--ios), box-shadow .5s var(--ios), filter .3s;}
.stButton > button:hover, .stDownloadButton > button:hover {border-color: #5E7A62; box-shadow: 0 12px 26px rgba(74,104,80,0.34);}
div[data-baseweb="slider"] div[role="slider"] {background: #5E7A62 !important; box-shadow: 0 0 0 5px rgba(94,122,98,0.16);}
div[data-baseweb="select"] > div:hover {border-color: #5E7A62 !important; box-shadow: 0 0 0 3px rgba(94,122,98,0.12);}
.insight {border-left-color: transparent;}
.insight::before {background: linear-gradient(180deg, #5E7A62, #A8B5A0);}
.ptrack {background: rgba(40,70,50,0.10); box-shadow: inset 0 1px 3px rgba(30,60,40,0.14);}
.pfill {box-shadow: 0 0 12px rgba(255,255,255,0.45) inset, 0 2px 10px rgba(30,60,40,0.18);}

section[data-testid="stSidebar"] {background: linear-gradient(180deg, rgba(255,255,255,0.55), rgba(232,240,228,0.46));
  box-shadow: 6px 0 30px rgba(30,60,40,0.07);}
section[data-testid="stSidebar"]::before {background: linear-gradient(90deg, #5E7A62, #A8B5A0);}
.brand .bm {background: linear-gradient(135deg, #1F2E25, #5E7A62); box-shadow: inset 0 1px 0 rgba(255,255,255,0.4), 0 6px 14px rgba(74,104,80,0.30);}
.brand .bt {font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;}

.hero {background: linear-gradient(135deg, #0F1A14 0%, #1C3326 55%, #2B4A37 100%);
       box-shadow: 0 24px 56px rgba(10,30,18,0.34), inset 0 1px 0 rgba(255,255,255,0.40), inset 0 -1px 0 rgba(255,255,255,0.08);}
.hero:hover {box-shadow: 0 30px 66px rgba(10,30,18,0.40), inset 0 1px 0 rgba(255,255,255,0.45), inset 0 -1px 0 rgba(255,255,255,0.10);}
.hero h1 {font-family: 'Plus Jakarta Sans', 'Segoe UI', sans-serif !important; font-weight: 800; letter-spacing: -0.02em;}
.hero .rule {background: linear-gradient(90deg, #C5D6B5, #E0C38C);}
.hero p {color: #D9E6D6;}
.hero .lq1 {background: #5E8F6A;} .hero .lq2 {background: #A8C48A;} .hero .lq3 {background: #2F6B55;} .hero .lq4 {background: #8FB09A;}
.hero .sphere {background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.90), rgba(255,255,255,0.20) 26%, rgba(255,255,255,0.05) 58%, rgba(190,225,190,0.26));
  box-shadow: inset -6px -8px 18px rgba(20,70,40,0.35), inset 4px 4px 10px rgba(255,255,255,0.50), 0 16px 30px rgba(5,25,12,0.32);}
.hero .w1 {animation-duration: 40s;} .hero .w2 {animation-duration: 30s;} .hero .w3 {animation-duration: 22s;}
.hero-art {filter: none;}
.ticker {background: linear-gradient(120deg, rgba(12,28,20,0.78), rgba(34,62,46,0.66)); border-color: rgba(255,255,255,0.22);
         box-shadow: 0 10px 28px rgba(10,30,18,0.22), inset 0 1px 0 rgba(255,255,255,0.28);}
.tk {border-right-color: rgba(255,255,255,0.18);} .tk p, .tk {color: #DDE9DA;} .tk i {color: #A6B8A4;}

.gk-big {color: #1E2A22;} .gk-sub {color: #5B685F;}
.gk-badge.ok {background: rgba(94,122,98,0.15); color: #3F5E46; border-color: rgba(94,122,98,0.32);}

/* ---- iOS-style motion: one easing curve, short travel, gentle springs ---- */
.gk, [data-testid="stPlotlyChart"], .pbar, [data-testid="stMetric"] {
  transition: transform .6s var(--ios), box-shadow .6s var(--ios), border-color .4s var(--ios), border-radius .6s var(--ios);}
.gk:hover {transform: translateY(-4px) scale(1.012); border-radius: 22px; box-shadow: 0 22px 48px rgba(30,60,40,0.17), inset 0 1px 0 #fff, inset 0 -1px 0 rgba(255,255,255,0.35);}
[data-testid="stPlotlyChart"]:hover {transform: translateY(-2px); border-radius: 22px; box-shadow: 0 20px 46px rgba(30,60,40,0.15), inset 0 1px 0 #fff, inset 0 -1px 0 rgba(255,255,255,0.35) !important;}
.pbar:hover {transform: translateX(3px);}
.gk {animation: gkin 1s var(--ios) backwards var(--d);}
[data-testid="stPlotlyChart"]::after, .gk::after {transition: transform 1.2s var(--ios);
  background: linear-gradient(115deg, transparent 40%, rgba(255,255,255,0.40) 50%, transparent 60%);}
.stTabs [data-baseweb="tab"] {transition: background .5s var(--ios), color .35s var(--ios), box-shadow .5s var(--ios), transform .5s var(--ios);}
.stTabs [data-baseweb="tab-panel"] {animation: fadeup .7s var(--ios) both;}
@keyframes fadeup {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: none;}}
@keyframes gkin {from {opacity: 0; transform: translateY(16px) scale(.985);} to {opacity: 1; transform: none;}}
@keyframes slidein {from {opacity: 0; transform: translateY(10px);} to {opacity: 1; transform: none;}}

/* =====================================================================
   THEME v4: transparent glass dashboard over a blurred warm interior
   ===================================================================== */
:root {--ink: #25211C; --muted: #6B6358; --line: rgba(255,255,255,0.55); --indigo: #2E8B78; --teal: #2E8B78; --orange: #F26B2A;
  --g-bg: linear-gradient(135deg, rgba(255,255,255,0.40), rgba(255,255,255,0.17));
  --g-brd: 1px solid rgba(255,255,255,0.64);
  --g-blur: blur(18px) saturate(1.35);
  --g-shadow: 0 10px 34px rgba(70,45,20,0.12), inset 0 1px 0 rgba(255,255,255,0.88), inset 0 -1px 0 rgba(255,255,255,0.25);}
.stApp {background: linear-gradient(180deg, #E8DFCF 0%, #D6C9B3 55%, #C9BAA2 100%);}
.stApp::before, .stApp::after {display: none;}
[data-testid="stHeader"] {background: transparent;}
.stApp, .stApp p, .stApp label, .stApp span, .stApp li {color: var(--ink);}
.stCaption, [data-testid="stCaptionContainer"] {color: var(--muted) !important;}

/* ---- the blurred room the glass sits on ---- */
.lgbg {background: linear-gradient(180deg, #E3D8C6 0%, #D8CBB5 45%, #C8B79D 100%);}
.lgbg::after {content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(120% 90% at 50% 40%, rgba(255,248,238,0.34), rgba(255,248,238,0.10) 60%, rgba(60,40,20,0.10) 100%);}
.lgbg i {position: absolute; display: block; width: auto; height: auto; border-radius: 48% / 50%; filter: blur(38px); opacity: .8;
         will-change: transform; animation: breathe var(--t, 28s) ease-in-out infinite alternate;}
.lgbg .s1 {left: -6vw; top: 1vh; width: 40vw; height: 17vh; background: #9A7250; opacity: .55; --t: 32s;}
.lgbg .s2 {right: -5vw; top: 2vh; width: 32vw; height: 20vh; background: #A67B54; opacity: .55; --t: 36s;}
.lgbg .s3 {left: 30vw; top: 9vh; width: 38vw; height: 24vh; background: #5A5550; opacity: .38; --t: 40s;}
.lgbg .s4 {left: 5vw; top: 4vh; width: 15vw; height: 11vh; background: #FFC27A; opacity: .85; --t: 22s;}
.lgbg .s5 {right: 9vw; top: 5vh; width: 13vw; height: 12vh; background: #FFB566; opacity: .8; --t: 25s;}
.lgbg .s6 {left: 18vw; top: 34vh; width: 42vw; height: 40vh; background: #FFF4E2; opacity: .85; --t: 30s;}
.lgbg .s7 {left: -4vw; bottom: -9vh; width: 108vw; height: 36vh; background: #B59878; opacity: .7; --t: 34s;}
.lgbg .s8 {right: 3vw; bottom: 17vh; width: 19vw; height: 22vh; background: #7D8B71; opacity: .5; --t: 26s;}
.lgbg .s9 {right: -6vw; bottom: -5vh; width: 36vw; height: 26vh; background: #7A5438; opacity: .55; --t: 38s;}
@keyframes breathe {0% {transform: translate3d(0,0,0) scale(1);} 100% {transform: translate3d(1.6vw, 1vh, 0) scale(1.07);}}

/* ---- one large glass frame holding the whole dashboard ---- */
.block-container {max-width: 1280px; margin: 18px auto 0; padding: 28px 30px 130px !important; border-radius: 34px;
  background: linear-gradient(135deg, rgba(255,255,255,0.16), rgba(255,255,255,0.06));
  border: 1px solid rgba(255,255,255,0.55); box-shadow: 0 24px 70px rgba(70,45,20,0.14), inset 0 1px 0 rgba(255,255,255,0.75);}
@media (max-width: 900px) {.block-container {padding: 18px 14px 120px !important; border-radius: 24px; margin-top: 8px;}}

/* ---- more transparent glass cards, rounder ---- */
[data-testid="stPlotlyChart"], .gk, .insight, .pbar, [data-testid="stMetric"], [data-testid="stDataFrame"] {border-radius: 26px;}
.gk:hover, [data-testid="stPlotlyChart"]:hover {border-radius: 26px;
  box-shadow: 0 20px 48px rgba(70,45,20,0.18), inset 0 1px 0 rgba(255,255,255,0.95), inset 0 -1px 0 rgba(255,255,255,0.3) !important;}
.gk-big, .gk-sub, .gk-top {text-shadow: none;}
.gk-big {color: var(--ink);} .gk-sub {color: var(--muted);}
.gk-badge.ok {background: rgba(46,139,120,0.16); color: #1F6B5B; border-color: rgba(46,139,120,0.35);}
.gk-badge.warn {background: rgba(242,107,42,0.16); color: #A3490F; border-color: rgba(242,107,42,0.38);}
.insight::before {background: linear-gradient(180deg, #2E8B78, #F26B2A);}
.ptrack {background: rgba(60,45,30,0.10); box-shadow: inset 0 1px 3px rgba(60,45,30,0.14);}
h3 {border-left-color: #2E8B78;}

/* ---- floating glass pill navigation (the tabs) ---- */
.stTabs [data-baseweb="tab-list"] {position: fixed; left: 50%; bottom: 20px; transform: translateX(-50%); z-index: 1000;
  width: max-content; max-width: min(94vw, 1020px); overflow-x: auto; padding: 6px; gap: 4px; border-radius: 999px;
  background: rgba(255,255,255,0.34) !important; border: 1px solid rgba(255,255,255,0.75) !important;
  box-shadow: 0 18px 44px rgba(60,40,20,0.24), inset 0 1px 0 rgba(255,255,255,0.95) !important;
  -webkit-backdrop-filter: blur(24px) saturate(1.45); backdrop-filter: blur(24px) saturate(1.45); scrollbar-width: none;}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {display: none;}
.stTabs [data-baseweb="tab"] {border-radius: 999px; padding: 9px 16px; color: #4A4137; font-weight: 600;}
.stTabs [data-baseweb="tab"]:hover {background: rgba(255,255,255,0.45); color: var(--ink);}
.stTabs [data-baseweb="tab"][aria-selected="true"], .stTabs [data-baseweb="tab"][aria-selected="true"]:hover {
  background: rgba(255,255,255,0.94); color: #25211C; border: 1px solid rgba(255,255,255,1);
  box-shadow: 0 6px 16px rgba(60,40,20,0.18), inset 0 1px 0 #fff;}
.stTabs [data-baseweb="tab-panel"] {padding-top: 10px;}

/* ---- dark pill buttons / tags like the references ---- */
.stButton > button, .stDownloadButton > button {border-radius: 999px; color: #FFFFFF; border: 1px solid rgba(255,255,255,0.22);
  background: linear-gradient(180deg, #34302B, #15120F); box-shadow: 0 10px 22px rgba(20,12,6,0.28), inset 0 1px 0 rgba(255,255,255,0.22);}
.stButton > button:hover, .stDownloadButton > button:hover {border-color: rgba(255,255,255,0.4); box-shadow: 0 14px 28px rgba(20,12,6,0.34);}
span[data-baseweb="tag"] {background: linear-gradient(180deg, #34302B, #15120F) !important; border-radius: 999px !important;}
div[data-baseweb="slider"] div[role="slider"] {background: #2E8B78 !important; box-shadow: 0 0 0 5px rgba(46,139,120,0.18);}
div[data-baseweb="select"] > div:hover {border-color: #2E8B78 !important; box-shadow: 0 0 0 3px rgba(46,139,120,0.14);}
div[data-baseweb="select"] > div {background: rgba(255,255,255,0.30) !important; border-radius: 16px !important;
  border-color: rgba(255,255,255,0.6) !important;}

/* ---- sidebar: translucent glass ---- */
section[data-testid="stSidebar"] {background: linear-gradient(180deg, rgba(255,255,255,0.34), rgba(255,255,255,0.14));
  -webkit-backdrop-filter: blur(22px) saturate(1.35); backdrop-filter: blur(22px) saturate(1.35);
  border-right: 1px solid rgba(255,255,255,0.6); box-shadow: 6px 0 30px rgba(70,45,20,0.08);}
section[data-testid="stSidebar"]::before {background: linear-gradient(90deg, #2E8B78, #F26B2A);}
.brand .bm {background: linear-gradient(135deg, #1F6B5B, #2E8B78);}
.brand .bt {color: var(--ink);}

/* ---- hero: light frosted glass with teal / orange liquid behind ---- */
.hero {background: linear-gradient(135deg, rgba(255,255,255,0.36), rgba(255,255,255,0.14)); border: 1px solid rgba(255,255,255,0.7);
  -webkit-backdrop-filter: blur(18px) saturate(1.35); backdrop-filter: blur(18px) saturate(1.35);
  box-shadow: 0 20px 56px rgba(70,45,20,0.14), inset 0 1px 0 rgba(255,255,255,0.92), inset 0 0 40px rgba(255,255,255,0.16);}
.hero:hover {box-shadow: 0 26px 66px rgba(70,45,20,0.18), inset 0 1px 0 #fff, inset 0 0 40px rgba(255,255,255,0.2);}
.hero h1 {color: var(--ink);}
.hero p {color: #5A5046;}
.hero .rule {background: linear-gradient(90deg, #2E8B78, #F26B2A);}
.hero .lq {filter: blur(34px); opacity: .62;}
.hero .lq1 {background: #2E8B78;} .hero .lq2 {background: #F28B50;} .hero .lq3 {background: #8FA484;} .hero .lq4 {background: #E3C48B;}
.hero .pane {background: linear-gradient(135deg, rgba(255,255,255,0.34), rgba(255,255,255,0.10)); border-color: rgba(255,255,255,0.7);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), inset 0 0 40px rgba(255,255,255,0.10);}
.hero .sphere {background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95), rgba(255,255,255,0.35) 26%, rgba(255,255,255,0.10) 58%, rgba(255,225,200,0.30));
  box-shadow: inset -6px -8px 18px rgba(150,100,60,0.26), inset 4px 4px 10px rgba(255,255,255,0.7), 0 14px 28px rgba(70,45,20,0.20);}
.hero .w1 path:nth-child(1) {fill: rgba(255,255,255,0.30);} .hero .w2 path:nth-child(1) {fill: rgba(255,240,225,0.34);}
.hero .w3 path:nth-child(1) {fill: rgba(255,255,255,0.44);} .hero .wv path:nth-child(2) {stroke: rgba(255,255,255,0.95);}
.hero .chips span {background: rgba(255,255,255,0.42); border: 1px solid rgba(255,255,255,0.8); color: var(--ink);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.9);}
.hero .chips span:hover {background: rgba(255,255,255,0.62);}
.hero-art g {stroke: rgba(60,45,30,0.12);}
.hero-art line[stroke-dasharray] {stroke: rgba(60,45,30,0.34);}
.hero-art .draw {stroke: #2E8B78;} .hero-art .endp {fill: #F26B2A;} .hero-art .halo {stroke: #F26B2A;}

/* ---- ticker as light glass ---- */
.ticker {background: linear-gradient(135deg, rgba(255,255,255,0.38), rgba(255,255,255,0.16)); border: 1px solid rgba(255,255,255,0.7);
  box-shadow: 0 10px 28px rgba(70,45,20,0.12), inset 0 1px 0 rgba(255,255,255,0.9);}
.tk {color: #4A4137; border-right-color: rgba(60,45,30,0.14);} .tk i {color: #7A6F62;} .tk em {color: #B4452E;} .tk span {color: #1F6B5B;}
.tk b {filter: none;}

/* ---- hero: realistic animated world map ---- */
.hero {min-height: 340px; display: flex; flex-direction: column; justify-content: center;}
.hero p {max-width: 44%;}
.hero .sphere {display: none;}
.hero-map {position: absolute; right: -2%; top: 8px; bottom: 8px; width: 63%; z-index: 2; pointer-events: none;
  -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 24%, #000 100%); mask-image: linear-gradient(90deg, transparent 0, #000 24%, #000 100%);}
.hm {position: absolute; inset: 0; width: 100%; height: 100%;}
.hm-clouds {opacity: .32; overflow: hidden;}
.hm-cl {will-change: transform; animation: hmcl 150s linear infinite;}
@keyframes hmcl {from {transform: translateX(0);} to {transform: translateX(-1000px);}}
.hm-scan {animation: hmscan 12s ease-in-out infinite; mix-blend-mode: screen;}
@keyframes hmscan {0% {transform: translateX(0);} 100% {transform: translateX(1160px);}}
.hm-flow {animation: hmflow 3s linear infinite;}
@keyframes hmflow {to {stroke-dashoffset: -56;}}
.hm-ring {transform-box: fill-box; transform-origin: center; animation: hmring 3.2s ease-out infinite;}
.hm-ring.r2 {animation-delay: 1.6s;}
@keyframes hmring {0% {transform: scale(.2); opacity: .9;} 100% {transform: scale(2.2); opacity: 0;}}
.hm-city {animation: hmtw 4.5s ease-in-out infinite;}
@keyframes hmtw {0%, 100% {opacity: .55;} 50% {opacity: 1;}}
.hm-lbl {font: 700 12px 'Inter', sans-serif; fill: #5A1F32; paint-order: stroke; stroke: rgba(255,255,255,0.85); stroke-width: 3px; letter-spacing: .3px;}
@media (max-width: 900px) {.hero-map {width: 100%; opacity: .35; -webkit-mask-image: none; mask-image: none;} .hero p {max-width: 100%;}}

/* ---- extra polish: gentle parallax and entrances ---- */
.lgbg {inset: -30px; transform: translate3d(calc(var(--mx, 0) * -18px), calc(var(--my, 0) * -12px), 0); transition: transform 1.1s var(--ios);}
.hero-map {transform: translate3d(calc(var(--mx, 0) * -10px), calc(var(--my, 0) * -6px), 0); transition: transform .9s var(--ios);}
.hero {animation: heroin 1.2s var(--ios) backwards;}
[data-testid="stPlotlyChart"] {animation: chartin .9s var(--ios) backwards;}
.ticker {animation: slidein .9s var(--ios) backwards .15s;}
@keyframes heroin {from {opacity: 0; transform: translateY(16px) scale(.985);}}
@keyframes chartin {from {opacity: 0; transform: translateY(16px) scale(.985);}}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {animation: none !important;}
}
</style>
"""
LGBG = ("<div class='lgbg'>" + "".join(f"<i class='s{k}'></i>" for k in range(1, 10)) + "</div>")

LG_JS = r"""
<script>
(function () {
  var P, D;
  try { P = window.parent; D = P.document; } catch (e) { return; }
  try { if (P.__lgCleanup) P.__lgCleanup(); } catch (e) {}
  if (!P.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  if (P.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var html = D.documentElement;

  var css = `
  html.lg-on, html.lg-on * {cursor: none !important;}
  html.lg-on input, html.lg-on textarea, html.lg-on [contenteditable="true"] {cursor: text !important;}
  #lg-layer {position: fixed; inset: 0; z-index: 2147483000; pointer-events: none; overflow: hidden;}
  .lg-bubble {position: absolute; left: 0; top: 0; width: 36px; height: 36px; border-radius: 50%; opacity: 0;
    will-change: transform, width, height;
    transition: opacity .3s ease, background .35s cubic-bezier(.32,.72,0,1), border-color .35s, box-shadow .35s;
    background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95), rgba(255,255,255,0.28) 24%, rgba(255,255,255,0.06) 56%, rgba(255,232,210,0.24));
    border: 1px solid rgba(255,255,255,0.75);
    box-shadow: inset -5px -7px 14px rgba(120,85,55,0.20), inset 4px 4px 9px rgba(255,255,255,0.65), 0 10px 24px rgba(70,45,20,0.20);
    -webkit-backdrop-filter: blur(2px) saturate(180%) brightness(1.07); backdrop-filter: blur(2px) saturate(180%) brightness(1.07);}
  .lg-bubble::after {content: ""; position: absolute; left: 20%; top: 14%; width: 30%; height: 17%; border-radius: 50%;
    background: rgba(255,255,255,0.92); filter: blur(1px); transform: rotate(-28deg); transition: opacity .25s;}
  .lg-bubble.hot {background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95), rgba(255,255,255,0.22) 26%, rgba(255,255,255,0.04) 60%, rgba(255,205,165,0.30));}
  .lg-bubble.morph {border-color: rgba(255,255,255,0.9);
    background: linear-gradient(180deg, rgba(255,255,255,0.24), rgba(255,255,255,0.07));
    box-shadow: 0 10px 28px rgba(70,45,20,0.14), inset 0 1px 0 rgba(255,255,255,0.95), inset 0 0 14px rgba(255,255,255,0.30);
    -webkit-backdrop-filter: blur(0.4px) saturate(170%) brightness(1.1); backdrop-filter: blur(0.4px) saturate(170%) brightness(1.1);}
  .lg-bubble.morph::after {opacity: 0;}
  .lg-ring {position: absolute; border-radius: 50%; box-sizing: border-box; opacity: 0; border-style: solid;
    border-color: rgba(255,255,255,0.95); will-change: transform, opacity;
    background: radial-gradient(circle, transparent 60%, rgba(255,255,255,0.14) 70%, transparent 76%);
    box-shadow: 0 0 0 1px rgba(110,80,50,0.16), inset 0 0 16px rgba(255,255,255,0.55), 0 0 18px rgba(255,255,255,0.40);}
  .lg-bead {position: absolute; border-radius: 50%; opacity: 0; will-change: transform, opacity;
    background: radial-gradient(circle at 32% 28%, #fff, rgba(255,255,255,0.5) 42%, rgba(150,110,70,0.26));
    box-shadow: 0 2px 6px rgba(70,45,20,0.24);}
  `;
  var style = D.createElement('style'); style.id = 'lg-style'; style.textContent = css; D.head.appendChild(style);
  var layer = D.createElement('div'); layer.id = 'lg-layer';
  var bubble = D.createElement('div'); bubble.className = 'lg-bubble';
  layer.appendChild(bubble); D.body.appendChild(layer);
  html.classList.add('lg-on');

  var MORPH = 'a, button, [role="tab"], [role="option"], summary, label[data-baseweb="radio"], label[data-baseweb="checkbox"], div[data-baseweb="select"]';
  var HOTONLY = '[role="slider"], [data-baseweb="slider"]';
  var D0 = 36;
  var px = -200, py = -200, bx = px, by = py, bw = D0, bh = D0, br = D0 / 2;
  var sc = 1, sv = 0, pressed = false, seen = false, raf = 0, last = 0, cur = null, lastEl = null, wasMorph = false, wasHot = false;

  function pick(el) {
    if (!el || !el.closest) return null;
    var m = el.closest(MORPH); if (m) return {el: m, morph: true};
    var h = el.closest(HOTONLY); return h ? {el: h, morph: false} : null;
  }

  function loop(t) {
    var dt = Math.min((t - last) / 1000, 0.05); if (!(dt > 0)) dt = 0.016; last = t;
    var f = dt * 60, kp = 1 - Math.exp(-dt * 34), kz = 1 - Math.exp(-dt * 17);
    var tcx = px, tcy = py, tw = D0, th = D0, tr = D0 / 2, morph = false, hot = false;
    if (cur) {
      var r = cur.el.getBoundingClientRect();
      if (!cur.el.isConnected || r.width < 1) { cur = null; }
      else if (cur.morph && r.height <= 64 && r.width <= 420) {
        morph = true;
        var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        tcx = cx + (px - cx) * 0.10; tcy = cy + (py - cy) * 0.12;
        tw = r.width + (r.height < 26 ? 10 : 14); th = r.height + (r.height < 26 ? 7 : 8); tr = Math.min(th / 2, 18);
      } else { hot = true; tw = th = D0 * 1.25; tr = tw / 2; }
    }
    if (morph !== wasMorph) { bubble.classList.toggle('morph', morph); wasMorph = morph; }
    if (hot !== wasHot) { bubble.classList.toggle('hot', hot); wasHot = hot; }
    var ox = bx, oy = by;
    bx += (tcx - bx) * kp; by += (tcy - by) * kp;
    bw += (tw - bw) * kz; bh += (th - bh) * kz; br += (tr - br) * kz;
    var vx = (bx - ox) / dt, vy = (by - oy) / dt;
    var ax = morph ? 0 : Math.min(Math.abs(vx) * 0.00028, 0.2), ay = morph ? 0 : Math.min(Math.abs(vy) * 0.00028, 0.2);
    var sx = 1 + ax - ay * 0.5, sy = 1 + ay - ax * 0.5;
    var target = pressed ? (morph ? 0.96 : 0.82) : 1;
    sv += (target - sc) * 0.22 * f; sv *= Math.pow(0.72, f); sc += sv * f;
    bubble.style.width = bw + 'px'; bubble.style.height = bh + 'px'; bubble.style.borderRadius = br + 'px';
    bubble.style.transform = 'translate3d(' + (bx - bw / 2) + 'px,' + (by - bh / 2) + 'px,0) scale(' + (sc * sx) + ',' + (sc * sy) + ')';
    raf = P.requestAnimationFrame(loop);
  }

  function onMove(e) {
    px = e.clientX; py = e.clientY;
    html.style.setProperty('--mx', (px / P.innerWidth - 0.5).toFixed(3)); html.style.setProperty('--my', (py / P.innerHeight - 0.5).toFixed(3));
    if (!seen) { seen = true; bx = px; by = py; bubble.style.opacity = 1; }
    if (e.target !== lastEl) { lastEl = e.target; cur = pick(e.target); }
  }
  function onLeave() { bubble.style.opacity = 0; seen = false; cur = null; lastEl = null; }

  function mk(cls, x0, y0, w, h) {
    var el = D.createElement('div'); el.className = cls;
    el.style.left = x0 + 'px'; el.style.top = y0 + 'px'; el.style.width = w + 'px'; el.style.height = h + 'px';
    el.style.marginLeft = (-w / 2) + 'px'; el.style.marginTop = (-h / 2) + 'px';
    layer.appendChild(el); return el;
  }
  function done(a, el) { a.onfinish = function () { if (el.parentNode) el.parentNode.removeChild(el); }; }

  function drop(cx, cy) {
    var ease = 'cubic-bezier(.22,1,.36,1)';
    var rings = [
      {d: 1700, del: 0,   size: 270, bw: 2.0, a: 0.90},
      {d: 1950, del: 150, size: 210, bw: 1.6, a: 0.65},
      {d: 2200, del: 300, size: 155, bw: 1.2, a: 0.46},
      {d: 2450, del: 470, size: 105, bw: 1.0, a: 0.30}
    ];
    rings.forEach(function (r) {
      var el = mk('lg-ring', cx, cy, r.size, r.size);
      var a = el.animate([
        {transform: 'scale(0.04)', opacity: 0, borderWidth: (r.bw * 2.4) + 'px'},
        {opacity: r.a, offset: 0.10},
        {opacity: r.a * 0.5, offset: 0.55},
        {transform: 'scale(1)', opacity: 0, borderWidth: (r.bw * 0.35) + 'px'}
      ], {duration: r.d, delay: r.del, easing: ease, fill: 'both'});
      done(a, el);
    });
    var bead = mk('lg-bead', cx, cy, 16, 16);
    done(bead.animate([{transform: 'scale(1.5)', opacity: 0.9}, {transform: 'scale(0)', opacity: 0}],
                      {duration: 460, easing: ease, fill: 'both'}), bead);
    for (var i = 0; i < 7; i++) {
      var ang = (Math.PI * 2 * i / 7) + Math.random() * 0.5, dist = 20 + Math.random() * 26, sz = 3 + Math.random() * 3;
      var dp = mk('lg-bead', cx, cy, sz, sz), c = Math.cos(ang), s = Math.sin(ang);
      done(dp.animate([
        {transform: 'translate(0,0) scale(1)', opacity: 0.85},
        {transform: 'translate(' + (c * dist) + 'px,' + (s * dist - 8) + 'px) scale(0.9)', opacity: 0.75, offset: 0.55},
        {transform: 'translate(' + (c * dist * 1.1) + 'px,' + (s * dist * 1.1 + 10) + 'px) scale(0.2)', opacity: 0}
      ], {duration: 650 + Math.random() * 180, easing: ease, fill: 'both'}), dp);
    }
  }

  function onDown(e) {
    if (e.button !== undefined && e.button !== 0) return;
    pressed = true; drop(e.clientX, e.clientY);
  }
  function onUp() { pressed = false; }

  D.addEventListener('pointermove', onMove, true);
  D.addEventListener('pointerdown', onDown, true);
  D.addEventListener('pointerup', onUp, true);
  html.addEventListener('mouseleave', onLeave);
  raf = P.requestAnimationFrame(loop);

  P.__lgCleanup = function () {
    P.cancelAnimationFrame(raf);
    html.style.removeProperty('--mx'); html.style.removeProperty('--my');
    D.removeEventListener('pointermove', onMove, true); D.removeEventListener('pointerdown', onDown, true);
    D.removeEventListener('pointerup', onUp, true); html.removeEventListener('mouseleave', onLeave);
    html.classList.remove('lg-on');
    var a = D.getElementById('lg-style'); if (a) a.remove();
    var b = D.getElementById('lg-layer'); if (b) b.remove();
  };
})();
</script>
"""

st.markdown(CSS.replace("__SCENE__", SCENE_URI), unsafe_allow_html=True)
st.markdown(LGBG, unsafe_allow_html=True)
st.components.v1.html(LG_JS, height=0)


@st.cache_data
def load():
    d = pd.read_csv("cleaned_data.csv")
    r = pd.read_csv("recovery_rates.csv")
    d["iso3"] = d["country"].map(ISO3)
    return d, r


df, rec = load()


def style(fig, h=450, bottom=10):
    """Common look for every chart: left title, legend on the right, no overlaps."""
    fig.update_layout(
        template="plotly_white", height=h,
        font=dict(family=FONT, size=13, color=NAVY),
        title=dict(x=0.01, xanchor="left", y=0.96, yanchor="top", font=dict(size=16, color=NAVY)),
        margin=dict(l=10, r=10, t=75, b=bottom),
        legend=dict(orientation="v", x=1.01, y=1, xanchor="left", yanchor="top",
                    bgcolor="rgba(0,0,0,0)", title_text=""),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="rgba(80,60,40,0.22)", font=dict(family=FONT, size=13, color=NAVY)),
        transition=dict(duration=500, easing="cubic-in-out"),
    )
    fig.update_xaxes(gridcolor="rgba(80,60,40,0.10)", linecolor="rgba(80,60,40,0.22)", zerolinecolor="rgba(80,60,40,0.16)")
    fig.update_yaxes(gridcolor="rgba(80,60,40,0.10)", linecolor="rgba(80,60,40,0.22)", zerolinecolor="rgba(80,60,40,0.16)")
    fig.update_polars(bgcolor="rgba(242,246,238,0.7)",
                      radialaxis=dict(gridcolor="rgba(80,60,40,0.16)"), angularaxis=dict(gridcolor="rgba(80,60,40,0.16)"))
    return fig


def kpi_cards_html(recs):
    """Glass KPI cards (rise in, numbers count up with CSS). Same figures as before."""
    cards = []
    for i, (_, row) in enumerate(recs.iterrows()):
        c = row["country"]
        drop = 100 - row["trough_index"]
        if pd.isna(row["years_to_recover"]):
            cls, txt = "warn", f'Still recovering · {row["pct_of_loss_regained"]:.0f}% regained'
        else:
            cls, txt = "ok", f'Recovered in {int(row["years_to_recover"])} yrs'
        cards.append(
            f'<div class="gk" style="--c:{COLORS[c]}; --d:{i * 0.13:.2f}s">'
            f'<div class="gk-top"><span class="gk-dot"></span>{c}</div>'
            f'<div class="gk-big">−<span class="count" style="--to:{drop:.0f}"></span>%</div>'
            f'<div class="gk-sub">GDP at its lowest ({int(row["trough_year"])})</div>'
            f'<span class="gk-badge {cls}">{txt}</span></div>'
        )
    return '<div class="gk-row">' + "".join(cards) + "</div>"


def draw_animation(data, countries):
    """Line chart that 'draws itself' year by year, with Play / Pause and a slider."""
    years = sorted(int(y) for y in data["years_since_war_start"].unique())

    def traces_upto(cutoff):
        out = []
        for c in countries:
            s = data[(data["country"] == c) & (data["years_since_war_start"] <= cutoff)]
            s = s.sort_values("years_since_war_start")
            out.append(go.Scatter(x=s["years_since_war_start"], y=s["GDP_index"], name=c,
                                  mode="lines+markers", line=dict(color=COLORS[c], width=3),
                                  marker=dict(size=7)))
        return out

    fig = go.Figure(data=traces_upto(years[0]),
                    frames=[go.Frame(data=traces_upto(y), name=str(y)) for y in years])
    ymin = max(0.0, float(data["GDP_index"].min()) - 10)
    ymax = float(data["GDP_index"].max()) * 1.08
    play = dict(frame=dict(duration=380, redraw=True), transition=dict(duration=250),
                fromcurrent=True, mode="immediate")
    pause = dict(frame=dict(duration=0, redraw=False), transition=dict(duration=0), mode="immediate")
    fig.update_layout(
        title="Recovery drawn year by year (press ▶)",
        xaxis=dict(range=[years[0] - 0.5, years[-1] + 0.5], title=""),
        yaxis=dict(range=[ymin, ymax], title=IDX_LABEL),
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.2, xanchor="left", yanchor="top",
                          showactive=False, bgcolor="#EEF3EA", bordercolor="rgba(80,60,40,0.22)",
                          font=dict(color=NAVY),
                          buttons=[dict(label="▶ Play", method="animate", args=[None, play]),
                                   dict(label="⏸ Pause", method="animate", args=[[None], pause])])],
        sliders=[dict(active=0, x=0.16, len=0.84, y=-0.2, xanchor="left", yanchor="top",
                      currentvalue=dict(prefix="Years since war start: "),
                      bgcolor="rgba(80,60,40,0.10)", activebgcolor="#5E7A62", bordercolor="rgba(80,60,40,0.22)",
                      steps=[dict(method="animate", label=str(y),
                                  args=[[str(y)], dict(mode="immediate", frame=dict(duration=300, redraw=True),
                                                       transition=dict(duration=200))])
                             for y in years])],
    )
    fig.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fig.add_vline(x=0, line_dash="dot", line_color="grey")
    return style(fig, 560, bottom=120)


# ---------- Sidebar ----------
st.sidebar.markdown(BRAND, unsafe_allow_html=True)
st.sidebar.header("🎛️ Filters")
countries = [c for c in ORDER if c in df["country"].unique()]
selected = st.sidebar.multiselect("Countries", countries, default=countries)
lo, hi = int(df["years_since_war_start"].min()), int(df["years_since_war_start"].max())
rng = st.sidebar.slider("Years since war start", lo, hi, (max(lo, -10), hi))
log_scale = st.sidebar.checkbox("Log scale (for the Overview chart)")
st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About this project"):
    st.write(
        "Real GDP index built from World Bank GDP growth rates, with 100 set to the "
        "last year before each war. Recovery is modelled as 100 − A·exp(−k·t) from the "
        "trough until the index regains 100."
    )
st.sidebar.caption("Data: World Bank Open Data. War dates: UCDP / historical record.")
st.sidebar.markdown("<div style='height:300px'></div>", unsafe_allow_html=True)

# ---------- Hero ----------
st.markdown(
    '<div class="hero">' + HERO_FX + HERO_ART +
    '<h1>Economic Impact of War</h1><div class="rule"></div>'
    '<p>How Iraq, Kuwait, Rwanda and Ukraine’s economies fell and recovered around major conflicts</p>'
    f'<div class="chips"><span>4 conflicts</span><span>{int(df["year"].min())}–{int(df["year"].max())}</span>'
    '<span>World Bank data</span><span>Python · Plotly · Streamlit</span></div></div>',
    unsafe_allow_html=True,
)

if not selected:
    st.warning("Select at least one country in the sidebar.")
    st.stop()

view = df[df["country"].isin(selected) & df["years_since_war_start"].between(*rng)]
if view.empty:
    st.info("No data for this filter. Widen the year range in the sidebar.")
    st.stop()
rec_sel = rec[rec["country"].isin(selected)].copy()

# ---------- Scrolling ticker (same figures as the KPI cards) ----------
if len(rec_sel):
    _items = []
    for _, _r in rec_sel.iterrows():
        _c = _r["country"]
        _status = ("still recovering · " + f'{_r["pct_of_loss_regained"]:.0f}% regained'
                   if pd.isna(_r["years_to_recover"]) else f'recovered in {int(_r["years_to_recover"])} yrs')
        _items.append(f'<div class="tk"><b style="color:{COLORS[_c]}">{_c.upper()}</b>'
                      f'<i>{int(_r["trough_year"])}</i><em>▼ −{100 - _r["trough_index"]:.0f}%</em>'
                      f'<span>{_status}</span></div>')
    _half = "".join(_items * max(1, math.ceil(6 / len(_items))))
    st.markdown(f'<div class="ticker"><div class="tk-track">{_half}{_half}</div></div>', unsafe_allow_html=True)

# ---------- Animated KPI cards ----------
if len(rec_sel):
    st.markdown(kpi_cards_html(rec_sel), unsafe_allow_html=True)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
    ["📈 Overview", "🎬 Animated story", "🔍 Country deep-dive", "🎨 Chart gallery",
     "⚖️ Compare all 4", "⏱️ Recovery", "🗺️ Map", "📋 Data"]
)

# =====================================================================
# Tab 1: Overview (switchable chart type)
# =====================================================================
with tab1:
    kind = st.radio("Chart type", ["Line", "Area", "Bar", "Scatter"], horizontal=True, key="overview_kind")
    lbl = {"years_since_war_start": "Years since war start", "GDP_index": IDX_LABEL, "country": ""}

    if kind == "Line":
        fig1 = px.line(view, x="years_since_war_start", y="GDP_index", color="country",
                       markers=True, color_discrete_map=COLORS, labels=lbl,
                       title="Line chart: real GDP index on one timeline")
        fig1.update_traces(line=dict(width=3))
    elif kind == "Area":
        fig1 = go.Figure()
        for c in selected:
            s = view[view["country"] == c].sort_values("years_since_war_start")
            fig1.add_trace(go.Scatter(x=s["years_since_war_start"], y=s["GDP_index"], name=c,
                                      mode="lines", fill="tozeroy", opacity=0.45,
                                      line=dict(color=COLORS[c], width=2)))
        fig1.update_layout(title="Area chart: real GDP index on one timeline",
                           xaxis_title=lbl["years_since_war_start"], yaxis_title=IDX_LABEL)
    elif kind == "Bar":
        fig1 = px.bar(view, x="years_since_war_start", y="GDP_index", color="country",
                      barmode="group", color_discrete_map=COLORS, labels=lbl,
                      title="Bar chart: real GDP index by year since war start")
    else:
        fig1 = px.scatter(view, x="years_since_war_start", y="GDP_index", color="country",
                          color_discrete_map=COLORS, labels=lbl,
                          title="Scatter chart: real GDP index, one dot per year")
        fig1.update_traces(marker=dict(size=9))

    fig1.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fig1.add_vline(x=0, line_dash="dot", line_color="grey",
                   annotation_text="War starts", annotation_position="top right")
    if log_scale:
        fig1.update_yaxes(type="log")
    st.plotly_chart(style(fig1, 480), use_container_width=True)

    lines = []
    done = rec_sel.dropna(subset=["years_to_recover"])
    if not done.empty:
        fast = done.loc[done["years_to_recover"].idxmin()]
        lines.append(f'⚡ <b>Fastest recovery:</b> {fast["country"]} regained its pre-war GDP in '
                     f'{int(fast["years_to_recover"])} years.')
        if len(done) > 1:
            slow = done.loc[done["years_to_recover"].idxmax()]
            lines.append(f'🐢 <b>Slowest recovery:</b> {slow["country"]} took '
                         f'{int(slow["years_to_recover"])} years.')
    if not rec_sel.empty:
        deep = rec_sel.loc[rec_sel["trough_index"].idxmin()]
        lines.append(f'📉 <b>Deepest fall:</b> {deep["country"]}, where GDP dropped '
                     f'{100 - deep["trough_index"]:.0f}% below its pre-war level in {int(deep["trough_year"])}.')
        for _, p in rec_sel[rec_sel["years_to_recover"].isna()].iterrows():
            lines.append(f'⏳ <b>{p["country"]}</b> has not recovered yet: '
                         f'{p["pct_of_loss_regained"]:.0f}% of the loss regained so far.')
    if lines:
        st.markdown('<div class="insight">' + "<br>".join(lines) + "</div>", unsafe_allow_html=True)

# =====================================================================
# Tab 2: Animated story
# =====================================================================
with tab2:
    st.markdown("### 🎬 Watch the story unfold")
    st.caption("Press ▶ under each chart. These use the countries and year range chosen in the sidebar.")

    st.markdown("#### 1 · The recovery, drawn year by year")
    st.plotly_chart(draw_animation(view, selected), use_container_width=True)

    a1, a2 = st.columns(2)

    with a1:
        st.markdown("#### 2 · Bar race")
        race = view.sort_values("years_since_war_start")
        fb = px.bar(race, x="country", y="GDP_index", color="country", color_discrete_map=COLORS,
                    animation_frame="years_since_war_start", text_auto=".0f",
                    range_y=[0, float(view["GDP_index"].max()) * 1.12],
                    labels={"GDP_index": IDX_LABEL, "country": "",
                            "years_since_war_start": "Years since war start"},
                    title="Bar race: GDP index at each point in time")
        fb.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
        fb.update_layout(showlegend=False)
        st.plotly_chart(style(fb, 480, bottom=100), use_container_width=True)

    with a2:
        st.markdown("#### 3 · Level vs growth")
        if "GDP_growth_pct" in view.columns:
            sc = view.dropna(subset=["GDP_growth_pct"]).sort_values("years_since_war_start").copy()
            sc["size"] = 20
            fs = px.scatter(sc, x="GDP_index", y="GDP_growth_pct", color="country", size="size",
                            size_max=24, text="country", animation_frame="years_since_war_start",
                            animation_group="country", color_discrete_map=COLORS,
                            range_x=[0, float(sc["GDP_index"].max()) * 1.1],
                            range_y=[float(sc["GDP_growth_pct"].min()) - 5, float(sc["GDP_growth_pct"].max()) + 5],
                            labels={"GDP_index": IDX_LABEL, "GDP_growth_pct": "Real GDP growth (%)",
                                    "years_since_war_start": "Years since war start"},
                            title="Bubbles move as years pass")
            fs.update_traces(textposition="top center")
            fs.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            fs.update_layout(showlegend=False)
            st.plotly_chart(style(fs, 480, bottom=100), use_container_width=True)
        else:
            st.info("No growth column in the data.")

# =====================================================================
# Tab 3: Country deep-dive
# =====================================================================
with tab3:
    one = st.selectbox("Choose a country", selected)
    sub = df[df["country"] == one]
    ws, we = int(sub["war_start"].iloc[0]), int(sub["war_end"].iloc[0])
    sub = sub[sub["year"] >= ws - 10]

    show_usd = False
    if "GDP_index_usd" in sub.columns:
        show_usd = st.checkbox("Also show the USD-based index (distorted by exchange rates)")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=sub["year"], y=sub["GDP_index"], mode="lines+markers",
                              name="Real GDP index",
                              line=dict(color=COLORS.get(one, NAVY), width=3)))
    if show_usd:
        fig2.add_trace(go.Scatter(x=sub["year"], y=sub["GDP_index_usd"], mode="lines",
                                  name="USD-based index", line=dict(dash="dot", color="grey")))
    fig2.add_vrect(x0=ws - 0.5, x1=we + 0.5, fillcolor="grey", opacity=0.22, line_width=0,
                   annotation_text="War years", annotation_position="top left")
    fig2.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fig2.update_layout(title=f"{one}: real GDP index", xaxis_title="Year", yaxis_title=IDX_LABEL)
    st.plotly_chart(style(fig2, 430), use_container_width=True)

    if "GDP_growth_pct" in sub.columns:
        g = sub.dropna(subset=["GDP_growth_pct"])
        bar_colors = [BAD if v < 0 else GOOD for v in g["GDP_growth_pct"]]
        fig2b = go.Figure(go.Bar(x=g["year"], y=g["GDP_growth_pct"], marker_color=bar_colors))
        fig2b.add_vrect(x0=ws - 0.5, x1=we + 0.5, fillcolor="grey", opacity=0.22, line_width=0)
        fig2b.update_layout(title=f"{one}: annual real GDP growth (%)",
                            xaxis_title="Year", yaxis_title="Growth %")
        st.plotly_chart(style(fig2b, 330), use_container_width=True)

# =====================================================================
# Tab 4: Chart gallery (same data, many chart types)
# =====================================================================
with tab4:
    st.markdown("### 🎨 The same story in different chart types")
    st.caption("Uses the countries and year range chosen in the sidebar.")

    g1, g2 = st.columns(2)

    with g1:
        if "Inflation_pct" in view.columns:
            inf = view.dropna(subset=["Inflation_pct"]).copy()
            inf["Inflation (%, capped at 100)"] = inf["Inflation_pct"].clip(upper=100)
            f = px.line(inf, x="year", y="Inflation (%, capped at 100)", color="country",
                        markers=True, color_discrete_map=COLORS, labels={"year": "Year", "country": ""},
                        title="Line: inflation over time")
            f.update_traces(line=dict(width=2.5))
            st.plotly_chart(style(f, 400), use_container_width=True)
        else:
            st.info("No inflation column in the data.")

    with g2:
        off = st.slider("Bar chart: years since war start", -5, 10, 2, key="off_bar")
        one_year = df[df["country"].isin(selected) & (df["years_since_war_start"] == off)]
        if one_year.empty:
            st.info("No country has data for that year. Try another value.")
        else:
            f = px.bar(one_year, x="country", y="GDP_index", color="country",
                       color_discrete_map=COLORS, text=one_year["GDP_index"].round(0),
                       labels={"GDP_index": IDX_LABEL, "country": ""},
                       title=f"Bar: GDP index at year {off:+d} (0 = war start)")
            f.update_traces(textposition="outside")
            f.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
            f.update_layout(showlegend=False)
            st.plotly_chart(style(f, 400), use_container_width=True)

    g3, g4 = st.columns(2)

    with g3:
        y_lo, y_hi = int(df["year"].min()), int(df["year"].max())
        yr = st.slider("Pie chart: year", y_lo, y_hi, y_hi, key="pie_year")
        py = df[df["country"].isin(selected) & (df["year"] == yr)].copy()
        if py.empty:
            st.info("No data for that year.")
        else:
            py["GDP (USD bn)"] = py["GDP_current_USD"] / 1e9
            f = px.pie(py, names="country", values="GDP (USD bn)",
                       color="country", color_discrete_map=COLORS,
                       title=f"Pie: share of combined GDP in {yr}")
            f.update_traces(textinfo="label+percent", marker=dict(line=dict(color="#FFFFFF", width=2)))
            st.plotly_chart(style(f, 400), use_container_width=True)

    with g4:
        f = go.Figure()
        for c in selected:
            s = view[view["country"] == c].sort_values("year")
            f.add_trace(go.Scatter(x=s["year"], y=s["GDP_current_USD"] / 1e9, name=c, mode="lines",
                                   fill="tozeroy", opacity=0.45, line=dict(color=COLORS[c], width=2)))
        f.update_layout(title="Area: size of each economy (USD bn)",
                        xaxis_title="Year", yaxis_title="GDP (USD bn)")
        st.plotly_chart(style(f, 400), use_container_width=True)

    g5, g6 = st.columns(2)

    with g5:
        if "GDP_growth_pct" in view.columns:
            sc2 = view.dropna(subset=["GDP_growth_pct"]).copy()
            sc2["size"] = sc2["GDP_growth_pct"].abs() + 1
            f = px.scatter(sc2, x="years_since_war_start", y="GDP_growth_pct", color="country",
                           size="size", size_max=22, opacity=0.7, color_discrete_map=COLORS,
                           labels={"years_since_war_start": "Years since war start",
                                   "GDP_growth_pct": "Real GDP growth (%)", "country": ""},
                           title="Bubble: yearly growth shocks")
            f.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            st.plotly_chart(style(f, 400), use_container_width=True)
        else:
            st.info("No growth column in the data.")

    with g6:
        if "GDP_growth_pct" in view.columns:
            bx = view.dropna(subset=["GDP_growth_pct"])
            f = px.box(bx, x="country", y="GDP_growth_pct", color="period",
                       color_discrete_map=PERIOD_COLORS,
                       labels={"GDP_growth_pct": "Real GDP growth (%)", "country": "", "period": ""},
                       title="Box plot: growth before, during, after war")
            f.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            st.plotly_chart(style(f, 400), use_container_width=True)

    pv = view.pivot_table(index="country", columns="years_since_war_start", values="GDP_index")
    z = pv.clip(lower=40, upper=250)
    fh = go.Figure(go.Heatmap(z=z.values, x=[int(c) for c in z.columns], y=list(z.index),
                              colorscale="RdYlGn", zmin=40, zmax=250, hoverongaps=False,
                              colorbar=dict(title="GDP index")))
    fh.update_layout(title="Heatmap: GDP index by country and year (green = strong, red = weak)",
                     xaxis_title="Years since war start")
    st.plotly_chart(style(fh, 330), use_container_width=True)

# =====================================================================
# Tab 5: Compare all four countries
# =====================================================================
with tab5:
    st.markdown("### ⚖️ All four countries side by side")
    st.caption("This tab always compares all four countries, whatever the sidebar filter says.")

    all_c = [c for c in ORDER if c in df["country"].unique() and c in rec["country"].values]
    latest = df.sort_values("year").groupby("country").tail(1).set_index("country")
    war_df = df[df["period"] == "during-war"]

    comp = rec.set_index("country").loc[all_c].copy()
    comp["GDP drop (%)"] = 100 - comp["trough_index"]
    comp["Latest index"] = latest["GDP_index"]
    comp["Latest year"] = latest["year"]
    comp["Peak war inflation (%)"] = (war_df.groupby("country")["Inflation_pct"].max()
                                      if "Inflation_pct" in df.columns else np.nan)
    comp["Avg war growth (%)"] = (war_df.groupby("country")["GDP_growth_pct"].mean()
                                  if "GDP_growth_pct" in df.columns else np.nan)

    st.markdown("#### 📊 Scorecard")
    score = comp.reset_index()[["country", "GDP drop (%)", "years_to_recover", "Latest index",
                                "Latest year", "Peak war inflation (%)", "Avg war growth (%)"]]
    score = score.rename(columns={"country": "Country", "years_to_recover": "Years to recover"})
    score = score.round(1).fillna("-")
    st.dataframe(score, hide_index=True, use_container_width=True)

    sm_data = df[df["country"].isin(all_c) & (df["years_since_war_start"] >= -10)]
    fm = px.line(sm_data, x="year", y="GDP_index", color="country", facet_col="country",
                 facet_col_wrap=2, color_discrete_map=COLORS,
                 labels={"year": "Year", "GDP_index": "GDP index"},
                 title="Four panels: each country on its own scale")
    fm.update_xaxes(matches=None, showticklabels=True)
    fm.update_yaxes(matches=None, showticklabels=True)
    fm.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fm.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.4)
    fm.update_layout(showlegend=False)
    st.plotly_chart(style(fm, 560), use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        gb = pd.concat([
            pd.DataFrame({"country": comp.index, "Point": "At trough", "GDP index": comp["trough_index"].values}),
            pd.DataFrame({"country": comp.index, "Point": "Latest year", "GDP index": comp["Latest index"].values}),
        ])
        fgb = px.bar(gb, x="country", y="GDP index", color="Point", barmode="group",
                     text=gb["GDP index"].round(0),
                     color_discrete_map={"At trough": BAD, "Latest year": GOOD},
                     labels={"country": ""},
                     title="Grouped bar: lowest point vs latest year")
        fgb.update_traces(textposition="outside")
        fgb.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
        st.plotly_chart(style(fgb, 420), use_container_width=True)

    with c2:
        rad = pd.DataFrame(index=comp.index)
        rad["Shock depth"] = comp["GDP drop (%)"]
        yrs = comp["years_to_recover"]
        worst = (yrs.max() if yrs.notna().any() else 0) + 2
        rad["Recovery time"] = yrs.fillna(worst)
        rad["Wartime inflation"] = comp["Peak war inflation (%)"].fillna(0).clip(upper=100)
        rad["Unrecovered loss"] = (100 - comp["Latest index"]).clip(lower=0)
        scaled = rad.div(rad.max().replace(0, np.nan)).fillna(0) * 100
        cats = list(scaled.columns)
        fr = go.Figure()
        for c in scaled.index:
            vals = scaled.loc[c].tolist()
            fr.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=cats + cats[:1], fill="toself",
                                         name=c, line=dict(color=COLORS[c]), opacity=0.55))
        fr.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                         title="Radar: how hard each country was hit")
        st.plotly_chart(style(fr, 420), use_container_width=True)
        st.caption("Larger area = harder hit. Each axis is scaled 0–100 against the worst country.")

    st.markdown("#### 🥊 Head to head")
    h1, h2 = st.columns(2)
    a = h1.selectbox("Country A", all_c, index=0, key="h2h_a")
    b = h2.selectbox("Country B", all_c, index=min(1, len(all_c) - 1), key="h2h_b")
    hh = df[df["country"].isin([a, b]) & (df["years_since_war_start"] >= -5)]
    fhh = px.line(hh, x="years_since_war_start", y="GDP_index", color="country", markers=True,
                  color_discrete_map=COLORS,
                  labels={"years_since_war_start": "Years since war start", "GDP_index": IDX_LABEL, "country": ""},
                  title=f"{a} vs {b}: real GDP index")
    fhh.add_hline(y=100, line_dash="dash", line_color="black", opacity=0.5)
    fhh.add_vline(x=0, line_dash="dot", line_color="grey")
    st.plotly_chart(style(fhh, 400), use_container_width=True)
    for box, name in ((h1, a), (h2, b)):
        rr = rec[rec["country"] == name]
        if not rr.empty:
            rr = rr.iloc[0]
            box.metric(f"{name}: GDP fall at trough", f"{100 - rr['trough_index']:.0f}%")
            if pd.isna(rr["years_to_recover"]):
                box.caption("Not back to its pre-war level yet.")
            else:
                box.caption(f"Back to its pre-war level in {int(rr['years_to_recover'])} years.")

# =====================================================================
# Tab 6: Recovery
# =====================================================================
with tab6:
    st.markdown("#### 🏁 Recovery progress")
    bars = ""
    for _, row in rec_sel.iterrows():
        pct = float(row["pct_of_loss_regained"]) if pd.notna(row["pct_of_loss_regained"]) else 0.0
        pct = max(0.0, min(100.0, pct))
        bars += (f'<div class="pbar"><div class="plabel"><b>{row["country"]}</b>'
                 f'<span>{pct:.0f}% of the loss regained</span></div>'
                 f'<div class="ptrack"><div class="pfill" style="width:{pct}%; '
                 f'background:{COLORS[row["country"]]}"></div></div></div>')
    st.markdown(bars, unsafe_allow_html=True)

    r = rec_sel.copy()
    r["trough_depth"] = 100 - r["trough_index"]
    r["years_plot"] = r["years_to_recover"].fillna(0)
    r["label"] = r["years_to_recover"].apply(lambda v: "not yet" if pd.isna(v) else str(int(v)))

    c1, c2 = st.columns(2)
    with c1:
        f = px.bar(r, x="country", y="trough_depth", color="country",
                   color_discrete_map=COLORS, text=r["trough_depth"].round(1),
                   title="How far GDP fell (index points lost)")
        f.update_traces(textposition="outside")
        f.update_layout(showlegend=False, xaxis_title="", yaxis_title="Points lost")
        st.plotly_chart(style(f, 400), use_container_width=True)
    with c2:
        f = px.bar(r, x="country", y="years_plot", color="country",
                   color_discrete_map=COLORS, text="label",
                   title="Years to regain the pre-war level")
        f.update_traces(textposition="outside")
        f.update_layout(showlegend=False, xaxis_title="", yaxis_title="Years")
        st.plotly_chart(style(f, 400), use_container_width=True)

    st.markdown("#### Recovery summary")
    nice = rec_sel.rename(columns={
        "country": "Country", "trough_year": "Trough year", "trough_index": "Trough index",
        "years_to_recover": "Years to recover", "pct_of_loss_regained": "% of loss regained",
        "shock_size_A": "Shock size (A)", "recovery_rate_k": "Recovery rate (k)",
        "half_life_yrs": "Half-life (yrs)"}).fillna("-")
    st.dataframe(nice, hide_index=True, use_container_width=True)
    st.caption("Model: index = 100 − A·exp(−k·t), fitted from the trough until the index regains 100. "
               "Fits for Iraq and Kuwait use only 3–4 points, so treat k as indicative. "
               "Ukraine has not recovered yet, so it shows progress instead of a fit.")

# =====================================================================
# Tab 7: Map
# =====================================================================
with tab7:
    m = view.copy().sort_values("year")
    m["GDP_index_capped"] = m["GDP_index"].clip(lower=40, upper=250)
    fig7 = px.choropleth(m, locations="iso3", color="GDP_index_capped",
                         hover_name="country", animation_frame="year",
                         color_continuous_scale="RdYlGn", range_color=(40, 250),
                         labels={"GDP_index_capped": "GDP index"},
                         title="GDP index by country, year by year (press ▶)")
    st.plotly_chart(style(fig7, 600, bottom=100), use_container_width=True)
    st.caption("Green = at or above the pre-war level, red = below it. Colour scale capped between 40 and 250.")

# =====================================================================
# Tab 8: Data
# =====================================================================
with tab8:
    want = ["country", "year", "period", "GDP_current_USD", "GDP_index", "GDP_index_usd",
            "GDP_growth_pct", "Inflation_pct"]
    show_cols = [c for c in want if c in view.columns]
    st.dataframe(view[show_cols], hide_index=True, use_container_width=True)
    st.download_button("⬇️ Download this data as CSV",
                       view[show_cols].to_csv(index=False).encode("utf-8"),
                       file_name="war_economy_filtered.csv", mime="text/csv")

st.markdown("---")
st.caption("Built with Python · pandas · SciPy · Plotly · Streamlit  |  Data: World Bank Open Data")
