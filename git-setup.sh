#!/bin/bash
# Git Setup Skript
# Führt die initiale Git-Konfiguration durch

echo "================================================"
echo "Git Setup für Trainingsplan Generator"
echo "================================================"
echo ""

# Prüfe ob Git installiert ist
if ! command -v git &> /dev/null; then
    echo "[FEHLER] Git ist nicht installiert!"
    echo "Bitte installiere Git von https://git-scm.com"
    exit 1
fi

echo "[OK] Git gefunden: $(git --version)"
echo ""

# Git Config (falls noch nicht gesetzt)
read -p "Git Benutzername: " git_username
read -p "Git Email: " git_email

git config --global user.name "$git_username"
git config --global user.email "$git_email"

echo "[OK] Git konfiguriert"
echo ""

# Prüfe ob bereits ein Repository existiert
if [ -d ".git" ]; then
    echo "[INFO] Git Repository existiert bereits"
    echo ""
else
    # Git initialisieren
    echo "[INFO] Initialisiere Git Repository..."
    git init
    git branch -M main
    echo "[OK] Git Repository erstellt"
    echo ""
fi

# Erstelle ersten Commit (falls noch keiner existiert)
if ! git rev-parse HEAD &> /dev/null; then
    echo "[INFO] Erstelle ersten Commit..."
    git add .
    git commit -m "Initial commit: Trainingsplan Generator mit Tests"
    echo "[OK] Erster Commit erstellt"
    echo ""
else
    echo "[INFO] Commits existieren bereits"
    echo ""
fi

# Remote Repository
echo "GitHub Repository einrichten?"
echo "1. Neues Repository auf GitHub erstellen: https://github.com/new"
echo "2. Repository URL kopieren (z.B. https://github.com/USERNAME/repo.git)"
echo ""

read -p "Möchtest du ein Remote Repository hinzufügen? (j/n): " add_remote

if [ "$add_remote" = "j" ] || [ "$add_remote" = "J" ]; then
    read -p "Repository URL: " repo_url
    
    # Entferne altes origin falls vorhanden
    git remote remove origin 2>/dev/null || true
    
    git remote add origin "$repo_url"
    echo "[OK] Remote Repository hinzugefügt"
    echo ""
    
    read -p "Jetzt pushen? (j/n): " do_push
    if [ "$do_push" = "j" ] || [ "$do_push" = "J" ]; then
        git push -u origin main
        echo "[OK] Code zu GitHub gepusht"
    fi
fi

echo ""
echo "================================================"
echo "Git Setup abgeschlossen!"
echo "================================================"
echo ""
echo "Nützliche Git-Befehle:"
echo "  git status              - Zeige Änderungen"
echo "  git add .               - Füge alle Änderungen hinzu"
echo "  git commit -m 'msg'     - Erstelle Commit"
echo "  git push                - Push zu GitHub"
echo "  git pull                - Pull von GitHub"
echo "  git log --oneline       - Zeige Commit-Historie"
echo ""
