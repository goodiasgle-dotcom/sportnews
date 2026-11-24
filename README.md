# Sport News GR

Το site σου με τα τελευταία αθλητικά νέα από την Ελλάδα και τον κόσμο.

## Τι κάνει αυτό το site;

- Παίρνει νέα από 14 αθλητικές ιστοσελίδες (Ελληνικές και Ευρωπαϊκές)
- Μεταφράζει τα ξενόγλωσσα νέα στα Ελληνικά
- Τα βάζει σε ένα ωραίο layout σαν το Facebook
- Ενημερώνεται αυτόματά κάθε 15 λεπτά
- Είναι δωρεάν στο GitHub Pages

## Βήμα 1: Δημιουργία λογαριασμού GitHub

1. Πήγαινε στο https://github.com
2. Πάτα "Sign up"
3. Γράψε το email σου και έναν κωδικό
4. Επίλεξε "Free" plan
5. Επιβεβαίωσε το email σου

## Βήμα 2: Ανέβασμα κώδικα στο GitHub

1. Άνοιξε το terminal (KDE: πάτα Alt+Space και γράψε "konsole")
2. Γράψε τις παρακάτω εντολές:

```bash
cd "/home/ch/Desktop/sport news/sport-news-site"
git init
git add .
git commit -m "First commit - Sport News GR"
```

3. Πήγαινε στο GitHub.com και δημιούργησε ένα νέο repository:
   - Πάτα "New" (πάνω δεξιά)
   - Γράψε όνομα: `sport-news-site`
   - ΜΗΝ τσεκάρεις "Add a README file"
   - Πάτα "Create repository"

4. Σύνδεσε τοπικό repo με το GitHub:
```bash
git remote add origin https://github.com/ΤΟ_ΟΝΟΜΑ_ΣΟΥ/sport-news-site.git
git branch -M main
git push -u origin main
```

## Βήμα 3: Ενεργοποίηση GitHub Pages

1. Πήγαινε στο repository σου στο GitHub
2. Πάτα "Settings" → "Pages" (αριστερά στο μενού)
3. Στο "Build and deployment" → Source: επίλεξε "GitHub Actions"
4. Το site θα χτιστεί αυτόματα με το push στο main branch!

## Βήμα 4: Ενεργοποίηση αυτόματης ενημέρωσης (GitHub Actions)

Το workflow τρέχει αυτόματα κάθε 15 λεπτά. Αν θες να τρέξει και χειροκίνητα:
1. Πήγαινε στο repository → "Actions" → "Fetch News & Highlights"
2. Πάτα "Run workflow"

## Βήμα 5: Προσαρμογή URL (προαιρετικό)

Αν το repository σου έχει διαφορετικό όνομα, πήγαινε στο:
- Settings → "Variables" → "Actions" → "New repository variable"
- Name: `HUGO_BASEURL`
- Value: `https://ΤΟ_ΟΝΟΜΑ_ΣΟΥ.github.io/sport-news-site/`

## Τοπική δοκιμή (προαιρετικό)

Αν θες να δοκιμάσεις στον υπολογιστή σου:

```bash
cd "/home/ch/Desktop/sport news/sport-news-site"
export PATH="/home/ch/.local/bin:$PATH"
hugo server
```

Μετά άνοιξε Firefox και πήγαινε στο `http://localhost:1313`

## Πώς λειτουργεί;

1. Κάθε 15 λεπτά, το GitHub Actions τρέχει (cron: `15 * * * *`)
2. Παίρνει νέα από 14 RSS feeds
3. Μεταφράζει τα ξένα στα ελληνικά (MyMemory API)
4. Χτίζει το site με Hugo
5. Ανεβαίνει στο GitHub Pages

## Πηγές Νέων

### Ελληνικές
- Gazzetta.gr
- Gazzetta Football
- Novasports
- Redaroume
- OPA.gr

### Αγγλικές
- BBC Sport
- Sky Sports
- The Guardian
- 101 Great Goals

### Ιταλικές
- Football Italia
- Get Italian Football News

### Γαλλικές
- Get French Football News

### Γερμανικές
- Get German Football News

### Ισπανικές
- Get Spanish Football News

## Highlights (Video)

Από YouTube κανάλια:
- **TV Broadcasters**: SKAI.gr, Open TV, Novasports
- **Club Channels**: PAOK, AEK, Olympiacos, Aris, Panathinaikos, OFI
- **News**: Score.gr

## Ελεύθερα εργαλεία που χρησιμοποιούμε

| Εργαλείο | Τι κάνει | Κόστος |
|----------|----------|--------|
| Hugo | Χτίζει το site | Δωρεάν |
| GitHub | Αποθηκεύει τον κώδικα | Δωρεάν |
| GitHub Actions | Ενημερώνει αυτόματα | Δωρεάν |
| GitHub Pages | Φιλοξενεί το site | Δωρεάν |
| MyMemory | Μεταφράζει | Δωρεάν (αόριστο) |

## Χαρακτηριστικά

- 🎯 **Μόνο ποδόσφαιρο** - Φιλτράρει αυτόματα μη-αθλητικό περιεχόμενο
- 🌍 **Πολυγλωσσικό** - Μεταφράζει αγγλικά/ιταλικά/γαλλικά/γερμανικά/ισπανικά στα ελληνικά
- 🔄 **Αυτόματη ενημέρωση** - Κάθε 15 λεπτά χωρίς παρέμβασή σου
- ♿ **Πρόσβαση για όλους** - ARIA labels, keyboard navigation, dark mode
- 📱 **Responsive** - Δουλεύει σε mobile, tablet, desktop
- 🧪 **Tested** - Unit tests για κρίσιμες συναρτήσεις

## Ερωτήματα;

Αν έχεις απορίες, άνοιξε ένα Issue στο GitHub!