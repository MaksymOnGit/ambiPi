# ambiPi
Külső szoftver mentes ambient light megoldás. A képelemzés és a led szalag irányítás teljes egészében a raspberry pi-on keresztül történik.
Az ambilight Philips cég által bevezetett fogalom ami két angol szó összevonásából keletkezett, az ambient és light. Magyarul ezt a térbeli hangzáshoz hasonlóan térbeli fénynek, megvilágításnak lehet nevezni.
Lényege, hogy "kiterjeszti" a kijelzőn látható képet a mögötte lévő falra. Ezt egy kijelző mögé rögzített ARGB LED szalag segítségével teszi, aminek egyes LED elemei a hozzájuk legközelebb lévő képszegmens átlag színével világítanak. Ezzel azt a hatást érve el, hogy a kijelző széle jobban elmosódik a mögötte lévő felülettel.

Raspberry Pi alapú megoldások eddig is voltak, viszont mindegyik különféle átalakítók összeláncolásával érték el a kép digitálisból analógba való átalakítását, mert csak így lehetett raspberry pi segítségével a képet megkapni. Az én megoldásom egy HDMI - CSI 2 átalakító segítségével a kamera porton és könyvtár segítségével kapja meg és elemzi a bejövő videó stream-et. Így az egész szerkezet, sokkal kisebb és kevesebb összetevőt igényel.

A munka a Mikroelektromechanikai rendszerek (GKLB_INTM020) tárgy keretében készült.
