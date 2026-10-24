# Skill: Ciclo di Rework Automatico
- Ogni volta che il Developer modifica o crea un file Python, il Tester deve generare o aggiornare la suite di test corrispondente.
- Il Tester deve eseguire il comando `pytest` nell'ambiente di esecuzione.
- Se l'Exit Code del terminale è diverso da 0, il Tester deve scrivere le motivazioni del fallimento in un report e risvegliare il Developer per una correzione immediata. Il ciclo si interrompe solo quando l'Exit Code è 0.