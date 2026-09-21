# Rapport hebdomadaire — tâche planifiée Windows

Le rapport se lance à la main quand on veut :

```powershell
cd C:\Dev\registre-sst-infra-qc
python scripts\rapport_hebdo.py
```

Pour qu'il se lance seul chaque lundi matin, une tâche planifiée suffit. Rien d'autre n'est automatisé : le rapport ne modifie ni le registre ni les livrables.

## Avant de planifier

1. Les exports eCompliance doivent être déposés dans `ingest\` — c'est le seul geste manuel qui reste. Sans export, la section « ce qui a bougé » reste sur l'état précédent et le dit.
2. L'index des procédures d'ANCRAGE doit être accessible :

```powershell
setx ANCRAGE_INDEX "C:\Dev\Telecon-SST-Agents\corpus\index-procedures.csv"
```

## Créer la tâche

Dans PowerShell, en une commande. Adapter le chemin de `python.exe` si nécessaire — `(Get-Command python).Source` le donne.

```powershell
$action  = New-ScheduledTaskAction -Execute "python.exe" `
           -Argument "scripts\rapport_hebdo.py" `
           -WorkingDirectory "C:\Dev\registre-sst-infra-qc"
$horaire = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 7:00am
$reglage = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
Register-ScheduledTask -TaskName "SST — rapport hebdomadaire Infra QC" `
  -Action $action -Trigger $horaire -Settings $reglage -Description `
  "Produit rapports\rapport_hebdo_AAAA-MM-JJ.md. Aucune écriture au registre. Validation humaine requise."
```

## Vérifier, lancer, retirer

```powershell
Get-ScheduledTask -TaskName "SST — rapport hebdomadaire Infra QC"
Start-ScheduledTask -TaskName "SST — rapport hebdomadaire Infra QC"     # essai immédiat
Get-ScheduledTaskInfo -TaskName "SST — rapport hebdomadaire Infra QC"   # dernier résultat
Unregister-ScheduledTask -TaskName "SST — rapport hebdomadaire Infra QC" -Confirm:$false
```

Un code de retour `0` signifie que le rapport a été écrit. Il se trouve dans `rapports\`, daté du jour.

## Ce que la tâche ne fait pas

- Elle n'envoie aucun courriel. Le rapport est en markdown, prêt à coller.
- Elle n'écrit rien dans `donnees\` ni dans les livrables.
- Elle ne ferme aucune action et ne porte aucun verdict.
- `rapports\` et `ingest\` restent hors du dépôt : les exports contiennent des noms.

## Si la tâche échoue

| Symptôme | Cause probable |
|---|---|
| Code de retour autre que 0 | Dépendances absentes : `python -m pip install -r requirements.txt` |
| « Index des procédures introuvable » dans le rapport | `ANCRAGE_INDEX` non défini, ou dépôt ANCRAGE déplacé |
| « Aucun export dans ingest » | Rien n'a été déposé cette semaine — ce n'est pas une erreur |
