#név   : netjogtarlekerdezo.py
#verzió: 1.0
#kelt  : 2018.10.24
#Python: 3.7.0
#szerző: Csuvár Miklós
#email : miklos.csuvar@gmail.com
#------------------------------
##Leírás:
##Az alkalmazás lekérdezi a net.jogtar.hu-ról a fájlból beolvasott jogszabálylista elemeinek hatályosságát, és az eredményt
##fájlba menti.
##1. Adatbekérés
##2. A jogszabálylista beolvasása.
##3. A jogszabály linkjének kikeresése.
##4. A jogszabály hatályosságának kikeresése.
##5. Az eredmények elmentése.
#------------------------------
#Könyvtárak és modulok beolvasása
from bs4 import BeautifulSoup
import re
import requests
import time
import random
#------------------------------
def adatbekeres():
    print("Adatbekérés kezdődik.")
    global jogszab_filename#A jogszabályok listája.
    global veletlen#A randomizálás szükségessége (i/n) a robotok kizárásának elkerüléséhez.
    global query1#A kereső keresőkifejezésének törzse.
    query1 = "https://net.jogtar.hu/"
    global query2#A kereső keresőkifejezésének maradéka.
    query2 = "gyorskereso?keyword="
    global query3#A találat eleje.
    query3 = "jogszabaly?docid="
    global hataly_regex
    hataly_regex = "A jogszabály(.*)mai(.*)napon(.*)hatályos(.*)állapota."
    global idoalap#Véletlen időtag sorsolása
    idoalap = 0#0 s és "idoalap" s között.
    global randomizalas
    randomizalas = False
    
    print("Adja meg a jogszabálylistát tartalmazó fájl nevét!")
    jogszab_filename = input("Fájlnév: ")
    print("Adja meg a keresőkifejezés alapját! Alapértelmezés: " + query1)
    tmp = input("query1: ")
    if tmp != "":
        query1 = tmp

    print("Adja meg a gyorskeresés maradékát! Alapértelmezés: " + query2)
    tmp = input("query2: ")
    if tmp != "":
        query2 = tmp

    print("Adja meg a gyorskeresés maradékát! Alapértelmezés: " + query3)
    tmp = input("query3: ")
    if tmp != "":
        query3 = tmp
    query4 = "/jogszabaly?docid="

    print("Adja meg a hatálykeresés reguláris kifejezését! Alapértelmezés: " + hataly_regex)
    tmp = input("hataly_regex: ")
    if tmp != "":
        hataly_regex = tmp

    print("Szükséges a lekérdezési időközöket randomizálni [i/n]? Alapértelmezés: nem.")
    veletlen = input("randomizálás: ")
    if veletlen != "i":
        randomizalas = False
    else:
        randomizalas = True
        idoalap = input("A véletlen időtagok sorsolása [s]: 0 - ")
        idoalap = abs(float(int(idoalap)))
#----------
def jogszablistabeolv():
 # Változók deklarálása
    global jogszab_ID#Ez a jogszabályszámot, évszámot, jogszabálytípust tartalmazó szakasz. Pl. 1996. évi CXVI. törvény.
    jogszab_ID = []
    global jogszab_title#Ez a jogszabály címének szöveges része. Pl. "az atomenergiáról".
    jogszab_title = []
    global letszam#A jogszabályok száma
    letszam = -1
    text = ""
    tmp = []

    print("jogszablistabeolv() indul.")

 #A jogszabályok listájának beolvasása fájlból.
    f1 = open(jogszab_filename, "rt", encoding = "utf-8-sig")
    text = f1.read()
    print("Beolvasott, nyers jogszabálylista:")#Ellenőrzéshez.
    print(text)#Ellenőrzéshez.

 #A jogszabályok zavaró formázásának megszüntetése.
    text = szovegreszcsere(text,"\t"," ")
    text = szovegreszcsere(text,"\r"," ")
    text = szovegreszcsere(text,"\f"," ")
    text = szovegreszcsere(text,"\v"," ")
    text = szovegreszcsere(text,"  "," ")
    text = szovegreszcsere(text," \n","\n")
    text = szovegreszcsere(text,"^[0-9][0-9]*\n","\n")#Oldalszámozás törlése
    text = szovegreszcsere(text,"\n\n","\n")#Dupla soremelés törlése
    text = szovegreszcsere(text,"törvény\n","törvény ")
    text = szovegreszcsere(text,"rendelet\n","rendelet ")
    text = szovegreszcsere(text,"  "," ")
    text = szovegreszcsere(text,"törvény ","törvény;;")
    text = szovegreszcsere(text,"rendelet ","rendelet;;")
    text = szovegreszcsere(text,"\s\n","\n")#Felesleges spacek törlése a szövegen belül.

    #Zavaró karakterek törlése
    text.strip('\n')
    text.strip('\s')
    text.strip('\n')
    text.strip('\s')
    print("Szövegrészcserék:")#Ellenőrzéshez.
    print(text)#Ellenőrzéshez.

 #A jogszabályok listája 1-1 sorának felbontása számszerű azonosítót és "cím"-et tartalmazó részekre.
    tmp = text.split("\n")
    for line in tmp:
        print(line)
    letszam = len(tmp)
##    print("Jogszabályok darabszáma: ", str(letszam))
##    i = 0
##    while i < letszam:
##        print("i = ", str(i))
##        print("letszam = ",letszam)
##        if tmp[i] == "":
##            tmp.pop(i)
##            letszam -= 1
##        i += 1
##    print("Rendeletkiigazítás:")#Ellenőrzéshez.
##    print(tmp)#Ellenőrzéshez
    
    for x in tmp:#A számszerű és a címszerű részek 1-1 listába rendezése.
        if x != "":
            #print("x: ",x)#Ellenőrzéshez
            tmp2 = x.split(";;")
            len_tmp2 = len(tmp2)
            #print("len_tmp2 = ", len_tmp2)
            if len_tmp2 > 1:
                y = tmp2[0]
                if ("rendelet" in y) and ("törvényerejű" not in y):
                    y = rendeletmodositas(y)
                    #print("Rendeletformázás: ",y)#Ellenőrzéshez
                    tmp2[0] = y
                    print(tmp2[0])
                jogszab_ID.append(tmp2[0])
                if len_tmp2 < 3:
                    print(tmp2)
                    jogszab_title.append(tmp2[1])
                else:
                     tmp_jogszab_title = tmp2[1]
                     j = 2
                     while j < len_tmp2:
                         tmp_jogszab_title = tmp_jogszab_title + " " + tmp2[j]
                         j += 1
                     #jogszab_title.append(tmp2[1])
                     jogszab_title.append(tmp_jogszab_title)
                tmp2.clear()
            else:
                jogszab_ID.append("Hiányos")
                jogszab_title.append("Hiányos")
        else:
            jogszab_ID.append("Nincs jogszabály")
            jogszab_title.append("Nincs jogszabály")



    letszam = len(jogszab_ID)
    print("A jogszabályok száma: " + str(letszam))
    print("jogszablistabeolv() lefutott.")
#----------
def szovegreszcsere(text,mit,mire):
    old = text
    new = ""
    while (re.search(mit, old, flags = 0) != None):
        searchObj = re.search(mit, old, flags = 0)
        talalat = searchObj.group()
        old = old.replace(talalat,mire)
    new = old
    return new
#----------
def rendeletmodositas(text):
    old = text
    new = ""
    searchObj1 = re.search("[0-9]{1,}/[0-9]{4}", old, flags = 0)
    talalat = searchObj1.group()
    new += talalat +". ("
    talalat= ""
    
    searchObj2 = re.search("[IVX]{1,4}", old, flags = 0)
    talalat = searchObj2.group()
    new += talalat +". "
    talalat= ""

    searchObj3 = re.search("(\.{1,})(\s{0,})[0-9]{1,2}(\s{0,})\.", old, flags = 0)
    talalat = searchObj3.group()
    talalat = talalat.strip(".")
    talalat = talalat.strip(" ")
    talalat = talalat.strip(".")
    talalat = talalat.strip(" ")
    new += talalat +"."
    talalat= ""

    searchObj4 = re.search("\)(.*)rendelet", old, flags = 0)
    talalat = searchObj4.group()
    new += talalat
    talalat= ""
    
    return new
#----------
def urlkereses(q1,q2,q3,q4):
    new2 = ""
    new3 = ""
    search = q1 + q2 + q4
    print("urlkereses: ", search)

    r = requests.get(search)
##    print("r: ",r)#Ellenőrzéshez
    soup = BeautifulSoup(r.content,"html.parser")
##    print("soup: ",soup)#Ellenőrzéshez
    tmp = str(soup.find_all("a"))
##    print("linkek a soupból:")#Ellenőrzéshez
##    print(tmp)#Ellenőrzéshez
    tmp = szovegreszcsere(tmp,"</a>,","</a>;;")
    links = tmp.split(";;")    
    new2 = q1
    new3 = q1
    for link in links:
        if ("operative" in link) and (">" + q4 + "</h2>" in link):
            print("Linket találtam:", link)
            q3_tmp = txt2regex(q3)
            kereso2 = q3_tmp + ".*" + ekezetesszokoz2pontcsillag(q4)
            kereso2 = ekezetesszokoz2pontcsillag(kereso2)
            print("Regex keresőkifejezés: ", kereso2)
            searchObj = re.search(kereso2, link, flags = 0)
            if searchObj != None:
                new2 = searchObj.group()
                print("Regex találat: ", new2)
                new3 = q1 + new2
            else:
                new3 = q1
            break
    print("urlkereses(url): ", new3)
    return new3
#----------
def hatalykereses(url):
    print("url: ", url)
    if url != query1:
        r = requests.get(url)
        soup = BeautifulSoup(r.content,"html.parser")
        tmp = str(soup)
        kereso = ekezetesszokoz2pontcsillag(hataly_regex)
        searchObj = re.search(kereso,tmp,flags = 0)
##        new = searchObj.group()
##        if new == None:
##            new = "Nincs adat."
        if searchObj != None:
            if searchObj.group() != None:
                new = searchObj.group()
            else:
                new = "Nincs adat."
        else:
            new = "Nincs adat."
    else:
        new = "Nincs adat."        
    print("hatalykereses(url): ", new)
    return new
#----------
def ekezetesszokoz2pontcsillag(string_old):
    new = string_old
    while (re.search('[áéíóöőúüűÁÉÍÓÖŐÚÜŰ\s]{1}', new, flags = 0) != None):
        searchObj = re.search('[áéíóöőúüűÁÉÍÓÖŐÚÜŰ\s]{1}', new, flags = 0)        
        talalat = searchObj.group()
        new = new.replace(talalat,".*")
    while (re.search('\.\.', new, flags = 0) != None):
        searchObj = re.search('\.\.', new, flags = 0)        
        talalat = searchObj.group()
        new = new.replace(talalat,".")
    while (re.search('\.\*\.\*', new, flags = 0) != None):
        searchObj = re.search('\.\*\.\*', new, flags = 0)        
        talalat = searchObj.group()
        new = new.replace(talalat,".*")
##    print("ekezetesszokoz2pontcsillag(string_old): ",new)
    return new
#----------
def txt2regex(txt):
    new = txt
    while (re.search('=', new, flags = 0) != None):
        searchObj = re.search('=', new, flags = 0)        
        talalat = searchObj.group()
        new = new.replace(talalat,".*")        
    while (re.search('\?', new, flags = 0) != None):
        searchObj = re.search('\?', new, flags = 0)        
        talalat = searchObj.group()
        new = new.replace(talalat,"#&@")
    while (re.search('#&@', new, flags = 0) != None):
        searchObj = re.search('#&@', new, flags = 0)        
        talalat = searchObj.group()
        new = new.replace(talalat,"\?")
    return new
#----------
#Az eredmények szövegfájlba mentése.
def eredmenymentes(list_hat,list_url):#A nem globális változókat meg kell adni.
    print("eredménymentés(): Indul.")
    ido1 = time.localtime()
    i = 0
    ido2 = ""
    while i < 6:
        if ido1[i] < 10:
            tmp = "0" + str(ido1[i])
        else:
            tmp = str(ido1[i])
        ido2 += tmp
        i += 1
    filename = jogszab_filename.strip(".txt") + "_" + ido2 + "_eredmeny.txt"
    f = open(filename, "w", encoding="utf-8")
    i = 0
    while (i < len(jogszab_ID)):
        #A jogszabály azonosítószámai, címe, a hatályossága és az azt megalapozó url.
        c = jogszab_ID[i] + ";" + jogszab_title[i] + ";" + list_hat[i] + ";" + list_url[i] + "\n"
        f.write(c)
        i += 1
    f.close()
    print("eredmenymentes(): Lefutott.")
#----------
#Véletlen időtag generálása a lekérdezések véletlenszeű időben indításához a robot kizárásának elkerülésére.
def randomido():
   new = random.randrange(0, idoalap, 100)
   return new
#----------
def elorehaladas(i,letszam):
    if i < 9:
        txt = "  " + str(i + 1)
    elif i < 99:
        txt = " " + str(i + 1)
    else:
        txt = str(i)
    s = txt + "/" + str(letszam) + " : " + jogszab_ID[i] + " " + jogszab_title[i] + " feldolgozása folyik."
    print("\n" + s)
#----------
def main():
    print("Programfutás indul.")
    jogszab_url = []
    jogszab_hat = []

    adatbekeres()
    jogszablistabeolv()
    i = 0
    if randomizalas == False:
        while i < letszam:
            elorehaladas(i,letszam)
            url = urlkereses(query1,query2,query3,jogszab_ID[i])
            jogszab_url.append(url)
            hataly = hatalykereses(url)
            jogszab_hat.append(hataly)
            i += 1
    else:
        elobb = 0
        kesobb = 0
        delta = 0
        while i < letszam:
            print("Time: " + str(time.clock()))
            elorehaladas(i,letszam)
            delta = randomido()
            kesobb = elobb + delta
            while (time.clock() < kesobb):
                print("Time: " + str(time.clock()))
            elobb = kesobb
            url = urlkereses(query1,query2,query3,jogszab_ID[i])
            jogszab_url.append(url)
            hataly = hatalykereses(url)
            jogszab_hat.append(hataly)
            i += 1

    eredmenymentes(jogszab_hat,jogszab_url)
    print("Programfutás vége.")
#------------------------------
# while 1:
main()
