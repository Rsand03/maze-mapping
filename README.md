# Taltech Robotite programmeerimine (ITI0201) final boss

## Mapping

Robot peab külastama kõiki "ruute" labürindis enne labürindist välja sõitmist. Labürint koosneb plokkidest, mis on 30 cm küljepikkusega. 
Peale kaardistamise lõppu ja peale labürindist välja sõitmist, peab robot kaardi välja trükkima tekstilisel kujul (näide allpool).

## Localization

Kaardistamise faasis peab robot külastama kõiki ruute ja koostama selle info alusel kaardi.

Peale seda faasi, liigutatakse robot juhuslikku kohta labürindis (roboti nurk on 90 kraadise sammuga, st 0, 90, 180 või 270) ja robot peab liikuma ühte kindlasse nurka (x=0, y=0 --> "vasakusse alumisse nurka"). Selle saavutamiseks peab robot ennast lokaliseerima kaardil õigesse kohta (sest peale liigutamist robot ei tea kus ta täpselt asub).

## Example

<table>
  <tr>
    <td>
      <img src="https://github.com/user-attachments/assets/ea9d5fdd-afbf-4eca-ab04-27f0a0d720d2" width="350">
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
