# Sport News GR

Το site σου με τα τελευταία αθλητικά νέα από την Ελλάδα και τον κόσμο.

## Τι κάνει αυτό το site;

- Παίρνει νέα από 14 αθλητικές ιστοσελίδες (Ελληνικές και Ευρωπαϊκές)
- Μεταφράζει τα ξενόγλωσσα νέα στα Ελληνικά
- Τα βάζει σε ένα ωραίο layout σαν το Facebook
- Ενημερώνεται αυτόματά κάθε 30-60 λεπτά
- Είναι δωρεάν στο Netlify

## Βήμα 1: Δημιουργία λογαριασμού GitHub

1. Πήγαινε στο https://github.com
2. Πάτα "Sign up"
3. Γράψε το email σου και έναν κωδικό
4. Επίλεξε "Free" plan
5. Επιβεβαίωσε το email σου

## Βήμα 2: Δημιουργία λογαριασμού Netlify

1. Πήγαινε στο https://app.netlify.com
2. Πάτα "Sign up"
3. Επίλεξε "Sign up with GitHub"
4. Ακολούθησε τα βήματα

## Βήμα 3: Ανέβασμα κώδικα στο GitHub

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

## Βήμα 4: Σύνδεση με Netlify

1. Πήγαινε στο https://app.netlify.com
2. Πάτα "Add new site" → "Import an existing project"
3. Επίλεξε "GitHub"
4. Βρες το repository `sport-news-site`
5. Netlify θα χτίσει το site μόνο του!

## Βήμα 5: Ενεργοποίηση αυτόματης ενημέρωσης

Στο GitHub:

1. Πήγαινε στο repository σου
2. Πάτα "Settings" → "Secrets and variables" → "Actions"
3. Πάτα "New repository secret"
4. Γράψε:
   - Name: `NETLIFY_AUTH_TOKEN`
   - Value: (παρακάτω πώς να το πάρεις)

5. Πάτα "New repository secret" ξανά:
   - Name: `NETLIFY_SITE_ID`
   - Value: (παρακάτω πώς να το πάρεις)

### Πώς παίρνεις τα tokens:

**NETLIFY_AUTH_TOKEN:**
1. Στο Netlify, πάτα avatar (πάνω δεξιά) → "User settings"
2. Πάτα "Applications"
3. Στο "Personal access tokens", πάτα "New access token"
4. Γράψε όνομα (π.χ. "github-actions")
5. Αντέγραψε το token

**NETLIFY_SITE_ID:**
1. Στο Netlify, πάτα στο site σου
2. "Site configuration" → "General"
3. Βρίσκεται κάτω από "Site information"

## Βήμα 6: Δοκιμή

Πήγαινε στο https://app.netlify.com → Site σου → "Deploys"
Πάρτα το URL (π.χ. `https://你的-site.netlify.app`)

Τέλος! Το site σου είναι live!

## Τοπική δοκιμή (προαιρετικό)

Αν θες να δοκιμάσεις στον υπολογιστή σου:

```bash
cd "/home/ch/Desktop/sport news/sport-news-site"
export PATH="/home/ch/.local/bin:$PATH"
hugo server
```

Μετά άνοιξε Firefox και πήγαινε στο `http://localhost:1313`

## Πώς λειτουργεί;

1. Κάθε 30-60 λεπτά, το GitHub Actions τρέχει
2. Παίρνει νέα από 14 RSS feeds
3. Μεταφράζει τα ξένα στα ελληνικά
4. Χτίζει το site
5. Ανεβαίνει στο Netlify

## Πηγές Νέων

### Ελληνικές
- Sport24.gr
- Gazzetta.gr
- Sportime.gr
- Novasports.gr

### Αγγλικές
- BBC Sport
- Sky Sports
- ESPN
- The Guardian

### Ιταλικές
- Football Italia
- Gazzetta dello Sport
- Sky Sport Italia

### Γαλλικές
- L'Equipe

### Γερμανικές
- Kicker

### Ισπανικές
- Marca

## Ελεύθερα εργαλεία που χρησιμοποιούμε

| Εργαλείο | Τι κάνει | Κόστος |
|----------|----------|--------|
| Hugo | Χτίζει το site | Δωρεάν |
| GitHub | Αποθηκεύει τον κώδικα | Δωρεάν |
| GitHub Actions | Ενημερώνει αυτόματα | Δωρεάν |
| Netlify | Φιλοξενεί το site | Δωρεάν |
| MyMemory | Μεταφράζει | Δωρεάν |

## Ερωτήματα;

Αν έχεις απορίες, ρώτα με!
