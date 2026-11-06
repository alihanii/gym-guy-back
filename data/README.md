# Exercise bank

`exercises.csv` is the whole exercise bank. Edit it (Excel, Numbers, Google Sheets or
a text editor; save as CSV, UTF-8) and restart `start.sh`, or run
`python manage.py import_exercise_list --images`.

| column | meaning |
|---|---|
| `name_en` | English name. Also the exercise's id: renaming creates a new exercise. |
| `title_fa` | Persian title shown in the app. |
| `muscle_group` | One of: Quadriceps, Chest, Full Body, Abdominals, Shoulders, Biceps, Glutes, Triceps, Upper Back, Lats, Cardio, Hamstrings, Calves, Forearms, Traps, Neck, Lower Back, Adductors, Abductors, Other |
| `image` | An `https://` link, or a file in `images/` written as `images/name.jpg`. May be empty. |

- Add a row to add an exercise; delete a row to remove it. Exercises users made themselves are never touched.
- Images are downloaded once and stored as WebP in `media/` (or S3). Change the `image` value to replace one.
