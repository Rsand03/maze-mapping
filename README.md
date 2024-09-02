# Robotite programmeerimine (ITI0201) final boss


[simulator](https://github.com/iti0201/simulation) 
[robot API](https://github.com/iti0201/robot)

## Kaardistamine

Robot peab külastama kõiki "ruute" labürindis enne labürindist välja sõitmist. Labürint koosneb plokkidest, mis on 30 cm küljepikkusega. 
Peale kaardistamise lõppu ja peale labürindist välja sõitmist, peab robot kaardi välja trükkima tekstilisel kujul (näide allpool).

## Lokaliseerimine

Kaardistamise faasis peab robot külastama kõiki ruute ja koostama selle info alusel kaardi.

Peale seda faasi, liigutatakse robot juhuslikku kohta labürindis (roboti nurk on 90 kraadise sammuga, st 0, 90, 180 või 270) ja robot peab liikuma ühte kindlasse nurka (x=0, y=0 --> "vasakusse alumisse nurka"). Selle saavutamiseks peab robot ennast lokaliseerima kaardil õigesse kohta (sest peale liigutamist robot ei tea kus ta täpselt asub).

## Näide

<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/ea9d5fdd-afbf-4eca-ab04-27f0a0d720d2" width="375">
    </td>
    <td>
      <pre>
?X?X?X?X?X?X?X?X?
  X X       X   X
? ? ? ?X?X? ? ? ?
X X       X X X X
? ? ? ?X?X? ? ? ?
X   X X       X X
?X?X? ? ?X?X? ? ?
X   X X X   X X X
? ? ? ? ? ? ?X? ?
X X X X   X     X
? ? ?X?X?X? ?X?X?
X X           X??
? ?X?X? ?X?X? ?X?
X   X           X
?X? ? ?X? ? ?X?X?
X   X X?X X     X
? ?X? ??? ?X? ? ?
X X   X?X X   X X
? ? ? ?X? ? ? ?X?
X   X     X X   X
? ?X? ?X? ? ?X?X?
X X     X       X
?X? ?X? ? ?X  ?X?
X   X?X X X     X
?X?X???X?X?X?X?X?
      </pre>
    </td>
  </tr>
</table>

# Lahendus

[Demovideo](https://www.dropbox.com/scl/fi/2hriuyzlyxli4qulzch42/M4-3.mp4?rlkey=x706wq4qr2juj62m47o0fbx9s&st=9sret2it&dl=0)

# Tööpõhimõte

## Diskreetne liikumine
- Rataste enkoodrite väärtuste jälgimise abil pöörab robot alati 90 kraadi, lihtsustatud PID kontroller tagab peale pööramist saavutatud nurga hoidmise ka otse sõitise ajal
- Iga otse sõitmine kestab ligikaudu 30cm, misjärel skännib robot IR sensorite abil ümbrust ja valib liikumissuuna
- Kui 30cm täitumisel on sein otse ees, siis liigub robot kalibreerimise eesmärgil seinast täpselt 67,5 mm kaugusele, misjärel on ta mõlemast seinast täpselt sama kaugel.

## Kaardistamine

- Iga pööramise ja sõitmise salvestab robot mälusse ning uuendab selle põhjal oma asukohta (x, y) ja kaarti (dictionary), mis prinditakse ka terminalis välja.
- Esialgu (kui kogu labürint pole veel kaardistatud) eelistab robot vasakule pööramist ehk jälgib oma vasakpoolset seina. Enneaegse labürindist väljumise korral pöörab robot tagasi.
- Peale tervele välisseinale ringi peale tegemist (juhul kui leidub veel avastamata ruute), muudab robot avastamata ruudu naabrusesse sattudes oma jälgitavat seina. Seeläbi pääseb ta ka labürindi keskosa pool olevate "saarte" juurde. (tulevikus asendada A* algoritmiga)

## Lokaliseerimine

- Peale kogu labürindi avastamist jääb robot seisma ja ootab ümbertõstmist. Ümbertõstmine võib tähendada nii suuna muutmist (robot ei saa sellest aru) kui ka teisele ruudule tõstmist.
- Ümbertõstmise järel hakkab robot oma "oletatava" suuna ning sensoritega skännitava ümbruse põhjal uut lokaliseerimise kaarti koostama. Kaart võib olla näiteks 180 keeratud.
- Peale iga sõitmist ja ümbruse skännimist üritab robot lokaliseerimise kaarti nelja erinevat pidi tegeliku kaardi peale sobitada.
- Protsess kestab kuni lokaliseerimise kaart sobitub päris kaardi peale ainult ühte kindlasse kohta. Selle põhjal korrigeerib robot oma suuna ning asukoha õigeks.
- Lokaliseerimise järel suundub robot punkti (0, 0) ja jääb seisma.
