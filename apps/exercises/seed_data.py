"""Original exercise bank, written for this project (not scraped from any app).

Each row: slug, English title, Persian title, Persian gym-slang aliases,
equipment, tracking type, primary muscle, secondary muscles, injury tags.
Aliases are what athletes actually write on paper programs in Iranian gyms,
and are what the search box and the future AI importer match against.
"""

BB, DB, MC = "barbell", "dumbbell", "machine"
WBW, ABW, BW = "weighted_bodyweight", "assisted_bodyweight", "reps_only"
KB, PL, BAND, OTH = "kettlebell", "plate", "resistance_band", "other"

WR, BWR, ABWR = "weight_reps", "bodyweight_reps", "assisted_bodyweight"
DUR, DURW, DISTD, WDIST, REPS = "duration", "duration_weight", "distance_duration", "weight_distance", "reps_only"


def E(slug, en, fa, aliases, equipment, tracking, primary, secondary=(), injuries=()):
    return {
        "slug": slug,
        "title_en": en,
        "title_fa": fa,
        "persian_aliases": list(aliases),
        "equipment": equipment,
        "tracking_type": tracking,
        "primary_muscle": primary,
        "secondary_muscles": list(secondary),
        "injury_warnings": list(injuries),
    }


EXERCISES = [
    # ---------------------------------------------------------------- chest
    E("bench_press_barbell", "Bench Press (Barbell)", "پرس سینه هالتر", ["پرس سینه", "پرس تخت هالتر", "پرس سینه صاف", "بنچ پرس"], BB, WR, "chest", ["triceps", "shoulders"], ["shoulder"]),
    E("incline_bench_press_barbell", "Incline Bench Press (Barbell)", "پرس بالاسینه هالتر", ["بالاسینه هالتر", "پرس شیبدار مثبت هالتر", "پرس بالا سینه"], BB, WR, "chest", ["shoulders", "triceps"], ["shoulder"]),
    E("decline_bench_press_barbell", "Decline Bench Press (Barbell)", "پرس زیرسینه هالتر", ["زیرسینه هالتر", "پرس شیبدار منفی", "پرس زیر سینه"], BB, WR, "chest", ["triceps"], ["shoulder"]),
    E("bench_press_dumbbell", "Bench Press (Dumbbell)", "پرس سینه دمبل", ["پرس دمبل تخت", "پرس سینه با دمبل", "پرس دمبل"], DB, WR, "chest", ["triceps", "shoulders"], ["shoulder"]),
    E("incline_press_dumbbell", "Incline Press (Dumbbell)", "پرس بالاسینه دمبل", ["بالاسینه دمبل", "پرس شیبدار دمبل"], DB, WR, "chest", ["shoulders", "triceps"], ["shoulder"]),
    E("chest_fly_dumbbell", "Chest Fly (Dumbbell)", "قفسه سینه دمبل", ["قفسه دمبل", "قفسه تخت", "فلای دمبل"], DB, WR, "chest", ["shoulders"], ["shoulder"]),
    E("incline_fly_dumbbell", "Incline Fly (Dumbbell)", "قفسه بالاسینه دمبل", ["قفسه شیبدار", "قفسه بالا سینه"], DB, WR, "chest", ["shoulders"], ["shoulder"]),
    E("cable_crossover", "Cable Crossover", "کراس‌اوور سیم‌کش", ["کراس اور", "قفسه سیمکش", "قفسه سینه سیم کش", "فلای سیمکش"], MC, WR, "chest", ["shoulders"]),
    E("chest_fly_machine", "Chest Fly (Machine)", "قفسه سینه دستگاه", ["پک دک", "فلای دستگاه", "پروانه سینه", "دستگاه قفسه"], MC, WR, "chest", ["shoulders"]),
    E("chest_press_machine", "Chest Press (Machine)", "پرس سینه دستگاه", ["پرس سینه دستگاهی", "دستگاه پرس سینه"], MC, WR, "chest", ["triceps", "shoulders"]),
    E("smith_bench_press", "Bench Press (Smith Machine)", "پرس سینه اسمیت", ["پرس اسمیت", "پرس سینه دستگاه اسمیت"], MC, WR, "chest", ["triceps", "shoulders"], ["shoulder"]),
    E("push_up", "Push Up", "شنای سوئدی", ["شنا سوئدی", "شنا", "پوش آپ"], BW, REPS, "chest", ["triceps", "shoulders", "abdominals"], ["wrist"]),
    E("chest_dip", "Chest Dip", "دیپ سینه", ["پارالل سینه", "دیپ پارالل"], BW, BWR, "chest", ["triceps", "shoulders"], ["shoulder"]),
    E("pullover_dumbbell", "Pullover (Dumbbell)", "پلاور دمبل", ["پول اور", "پلاور", "دمبل پشت سر خوابیده"], DB, WR, "chest", ["lats", "triceps"], ["shoulder"]),

    # ------------------------------------------------------------- back
    E("deadlift_barbell", "Deadlift (Barbell)", "ددلیفت هالتر", ["ددلیفت", "لیفت مرده", "ددلیفت معمولی"], BB, WR, "lower_back", ["glutes", "hamstrings", "traps", "forearms", "quadriceps"], ["lower_back", "hip"]),
    E("romanian_deadlift_barbell", "Romanian Deadlift (Barbell)", "ددلیفت رومانیایی هالتر", ["رومانیایی", "ددلیفت رومانی", "ددلیفت پا صاف", "آر دی ال"], BB, WR, "hamstrings", ["glutes", "lower_back"], ["lower_back"]),
    E("bent_over_row_barbell", "Bent Over Row (Barbell)", "زیربغل هالتر خم", ["زیربغل خم هالتر", "روئینگ هالتر", "زیر بغل هالتر"], BB, WR, "upper_back", ["lats", "biceps", "lower_back"], ["lower_back"]),
    E("t_bar_row", "T-Bar Row", "زیربغل تی‌بار", ["تی بار", "زیربغل تی", "قایقی تی بار"], BB, WR, "upper_back", ["lats", "biceps"], ["lower_back"]),
    E("dumbbell_row", "Dumbbell Row", "زیربغل دمبل تک‌خم", ["زیربغل تک دمبل", "روئینگ دمبل", "اره کشی", "زیربغل دمبل"], DB, WR, "lats", ["upper_back", "biceps"]),
    E("lat_pulldown_cable", "Lat Pulldown (Cable)", "لت از جلو سیم‌کش", ["لت جلو", "لت دست باز", "زیربغل سیمکش از جلو", "لت سیم کش", "لت پولدان"], MC, WR, "lats", ["biceps", "upper_back"]),
    E("lat_pulldown_close_grip", "Lat Pulldown - Close Grip (Cable)", "لت دست جمع", ["لت دست بسته", "لت مثلثی", "زیربغل سیمکش دست جمع"], MC, WR, "lats", ["biceps", "upper_back"]),
    E("lat_pulldown_reverse_grip", "Lat Pulldown - Reverse Grip (Cable)", "لت دست برعکس", ["لت معکوس", "لت دست زیر"], MC, WR, "lats", ["biceps"]),
    E("behind_neck_pulldown", "Behind the Neck Pulldown", "لت از پشت", ["لت پشت گردن", "زیربغل سیمکش از پشت"], MC, WR, "lats", ["upper_back", "biceps"], ["shoulder", "neck"]),
    E("seated_cable_row", "Seated Cable Row", "زیربغل قایقی", ["قایقی", "روئینگ نشسته", "زیربغل سیمکش نشسته", "قایقی دست جمع"], MC, WR, "upper_back", ["lats", "biceps"]),
    E("seated_row_machine", "Seated Row (Machine)", "زیربغل دستگاه نشسته", ["روئینگ دستگاه", "زیربغل دستگاه"], MC, WR, "upper_back", ["lats", "biceps"]),
    E("straight_arm_pulldown", "Straight Arm Pulldown (Cable)", "پول‌داون دست صاف", ["لت دست صاف", "پول داون", "زیربغل دست صاف ایستاده"], MC, WR, "lats", ["triceps"]),
    E("pull_up", "Pull Up", "بارفیکس", ["بارفیکس دست باز", "بارفیکس از جلو", "پول آپ"], BW, BWR, "lats", ["biceps", "upper_back", "forearms"], ["shoulder"]),
    E("chin_up", "Chin Up", "بارفیکس دست برعکس", ["بارفیکس دست جمع", "چین آپ", "بارفیکس دست زیر"], BW, BWR, "lats", ["biceps"], ["elbow"]),
    E("weighted_pull_up", "Pull Up (Weighted)", "بارفیکس با وزنه", ["بارفیکس وزنه دار", "بارفیکس با کمربند"], WBW, BWR, "lats", ["biceps", "upper_back"], ["shoulder"]),
    E("assisted_pull_up", "Pull Up (Assisted)", "بارفیکس کمکی", ["دستگاه بارفیکس کمکی", "بارفیکس دستگاه"], ABW, ABWR, "lats", ["biceps", "upper_back"]),
    E("hyperextension", "Back Extension (Hyperextension)", "فیله کمر خرک", ["فیله کمر", "هایپر اکستنشن", "کمر خرک"], BW, BWR, "lower_back", ["glutes", "hamstrings"], ["lower_back"]),
    E("good_morning_barbell", "Good Morning (Barbell)", "گودمورنینگ هالتر", ["گود مورنینگ", "صبح بخیر"], BB, WR, "hamstrings", ["lower_back", "glutes"], ["lower_back"]),
    E("shrug_barbell", "Shrug (Barbell)", "کول هالتر", ["شراگ هالتر", "کول از جلو"], BB, WR, "traps", ["forearms"], ["neck"]),
    E("shrug_dumbbell", "Shrug (Dumbbell)", "کول دمبل", ["شراگ دمبل", "کول با دمبل"], DB, WR, "traps", ["forearms"], ["neck"]),
    E("rack_pull", "Rack Pull", "رک پول", ["ددلیفت از روی پایه", "ددلیفت نیمه"], BB, WR, "upper_back", ["lower_back", "traps", "glutes"], ["lower_back"]),

    # --------------------------------------------------------- shoulders
    E("overhead_press_barbell", "Overhead Press (Barbell)", "پرس سرشانه هالتر ایستاده", ["پرس سرشانه هالتر", "پرس نظامی", "پرس بالای سر", "سرشانه هالتر از جلو"], BB, WR, "shoulders", ["triceps", "traps", "abdominals"], ["shoulder", "lower_back"]),
    E("seated_shoulder_press_dumbbell", "Seated Shoulder Press (Dumbbell)", "پرس سرشانه دمبل نشسته", ["سرشانه دمبل", "پرس سرشانه دمبل", "پرس دمبل نشسته"], DB, WR, "shoulders", ["triceps"], ["shoulder"]),
    E("arnold_press", "Arnold Press (Dumbbell)", "پرس آرنولد", ["سرشانه آرنولد", "آرنولدی"], DB, WR, "shoulders", ["triceps"], ["shoulder"]),
    E("shoulder_press_machine", "Shoulder Press (Machine)", "پرس سرشانه دستگاه", ["سرشانه دستگاه", "دستگاه پرس سرشانه"], MC, WR, "shoulders", ["triceps"]),
    E("lateral_raise_dumbbell", "Lateral Raise (Dumbbell)", "نشر از جانب دمبل", ["نشر جانب", "نشر از بغل", "نشر دمبل از جانب", "جانب دمبل"], DB, WR, "shoulders", ["traps"], ["shoulder"]),
    E("lateral_raise_cable", "Lateral Raise (Cable)", "نشر از جانب سیم‌کش", ["نشر سیمکش", "نشر جانب سیم کش تک"], MC, WR, "shoulders", ["traps"]),
    E("front_raise_dumbbell", "Front Raise (Dumbbell)", "نشر از جلو دمبل", ["نشر جلو", "سرشانه جلو دمبل"], DB, WR, "shoulders", ["chest"]),
    E("front_raise_plate", "Front Raise (Plate)", "نشر از جلو با صفحه", ["نشر جلو صفحه", "فرمون", "نشر با وزنه صفحه"], PL, WR, "shoulders", ["chest"]),
    E("rear_delt_fly_dumbbell", "Rear Delt Fly (Dumbbell)", "نشر خم دمبل", ["نشر از خم", "سرشانه از پشت", "دلتوئید خلفی دمبل"], DB, WR, "shoulders", ["upper_back"]),
    E("reverse_fly_machine", "Reverse Fly (Machine)", "قفسه معکوس دستگاه", ["پک دک معکوس", "پروانه برعکس", "سرشانه پشت دستگاه"], MC, WR, "shoulders", ["upper_back"]),
    E("face_pull_cable", "Face Pull (Cable)", "فیس‌پول سیم‌کش", ["فیس پول", "صورت کش", "طناب به صورت"], MC, WR, "shoulders", ["upper_back", "traps"]),
    E("face_pull_band", "Face Pull (Band)", "فیس‌پول با کش", ["فیس پول کش", "کش به صورت"], BAND, WR, "shoulders", ["upper_back"]),
    E("upright_row_barbell", "Upright Row (Barbell)", "کول از جلو هالتر (اپرایت رو)", ["اپرایت رو", "کول جلو", "نشر هالتر از جلو تا چانه"], BB, WR, "traps", ["shoulders", "biceps"], ["shoulder", "wrist"]),

    # ------------------------------------------------------------- biceps
    E("bicep_curl_barbell", "Bicep Curl (Barbell)", "جلوبازو هالتر", ["جلو بازو هالتر", "جلوبازو ایستاده هالتر", "کرل هالتر"], BB, WR, "biceps", ["forearms"], ["elbow", "wrist"]),
    E("ez_bar_curl", "EZ Bar Curl", "جلوبازو هالتر خمیده (EZ)", ["جلوبازو ای زد", "جلوبازو هالتر ای زد", "هالتر خمیده جلوبازو"], BB, WR, "biceps", ["forearms"], ["elbow"]),
    E("bicep_curl_dumbbell", "Bicep Curl (Dumbbell)", "جلوبازو دمبل", ["جلو بازو دمبل", "جلوبازو دمبل جفت", "جلوبازو دمبل یک در میان"], DB, WR, "biceps", ["forearms"], ["elbow"]),
    E("hammer_curl_dumbbell", "Hammer Curl (Dumbbell)", "جلوبازو دمبل چکشی", ["چکشی", "جلو بازو چکشی", "همر"], DB, WR, "biceps", ["forearms"]),
    E("preacher_curl", "Preacher Curl", "جلوبازو لاری", ["لاری", "جلوبازو میز لاری", "لاری هالتر"], BB, WR, "biceps", ["forearms"], ["elbow"]),
    E("preacher_curl_machine", "Preacher Curl (Machine)", "جلوبازو لاری دستگاه", ["لاری دستگاه", "دستگاه جلوبازو"], MC, WR, "biceps", [], ["elbow"]),
    E("concentration_curl", "Concentration Curl", "جلوبازو تمرکزی", ["تمرکزی", "جلوبازو نشسته تک"], DB, WR, "biceps", []),
    E("incline_curl_dumbbell", "Incline Curl (Dumbbell)", "جلوبازو دمبل روی میز شیبدار", ["جلوبازو شیبدار", "جلوبازو خوابیده"], DB, WR, "biceps", [], ["shoulder"]),
    E("cable_curl", "Bicep Curl (Cable)", "جلوبازو سیم‌کش", ["جلوبازو سیمکش", "جلو بازو کابل"], MC, WR, "biceps", ["forearms"]),
    E("band_curl", "Bicep Curl (Band)", "جلوبازو با کش", ["جلوبازو کش"], BAND, WR, "biceps", []),
    E("plate_curl", "Plate Curl", "جلوبازو با صفحه", ["جلوبازو صفحه", "فرمون جلوبازو"], PL, WR, "biceps", ["forearms"]),

    # ------------------------------------------------------------ triceps
    E("triceps_pushdown_cable", "Triceps Pushdown (Cable)", "پشت بازو سیم‌کش", ["پشت بازو سیمکش", "پشت بازو ایستاده سیم کش", "پوش داون"], MC, WR, "triceps", [], ["elbow"]),
    E("triceps_rope_pushdown", "Triceps Rope Pushdown", "پشت بازو طناب", ["پشت بازو با طناب", "طناب پشت بازو"], MC, WR, "triceps", [], ["elbow"]),
    E("skull_crusher_ez", "Skull Crusher (EZ Bar)", "پشت بازو هالتر خوابیده", ["جمجمه شکن", "پشت بازو خوابیده", "اسکال کراشر"], BB, WR, "triceps", [], ["elbow"]),
    E("overhead_triceps_extension_dumbbell", "Overhead Triceps Extension (Dumbbell)", "پشت بازو دمبل از پشت سر", ["پشت بازو دمبل جفت", "پشت بازو نشسته دمبل", "فرانسوی دمبل"], DB, WR, "triceps", [], ["elbow", "shoulder"]),
    E("overhead_triceps_extension_cable", "Overhead Triceps Extension (Cable)", "پشت بازو سیم‌کش از پشت سر", ["پشت بازو طناب از پشت سر", "فرانسوی سیمکش"], MC, WR, "triceps", [], ["elbow"]),
    E("triceps_kickback_dumbbell", "Triceps Kickback (Dumbbell)", "پشت بازو دمبل خم", ["کیک بک", "پشت بازو تک دمبل خم"], DB, WR, "triceps", []),
    E("close_grip_bench_press", "Close Grip Bench Press", "پرس سینه دست جمع", ["پرس دست جمع", "پشت بازو پرس دست جمع"], BB, WR, "triceps", ["chest", "shoulders"], ["wrist", "elbow"]),
    E("triceps_dip", "Triceps Dip", "دیپ پشت بازو", ["پارالل", "دیپ", "پارالل پشت بازو"], BW, BWR, "triceps", ["chest", "shoulders"], ["shoulder", "elbow"]),
    E("weighted_dip", "Dip (Weighted)", "پارالل با وزنه", ["دیپ وزنه دار", "پارالل با کمربند"], WBW, BWR, "triceps", ["chest", "shoulders"], ["shoulder", "elbow"]),
    E("assisted_dip", "Dip (Assisted)", "پارالل کمکی", ["دستگاه پارالل کمکی", "دیپ کمکی"], ABW, ABWR, "triceps", ["chest"]),
    E("bench_dip", "Bench Dip", "پشت بازو روی نیمکت", ["دیپ نیمکت", "پشت بازو نیمکت"], BW, REPS, "triceps", ["shoulders"], ["shoulder", "wrist"]),
    E("diamond_push_up", "Diamond Push Up", "شنای دست جمع", ["شنا الماسی", "شنا دست جمع"], BW, REPS, "triceps", ["chest"], ["wrist"]),

    # ------------------------------------------------------------ forearms
    E("wrist_curl_barbell", "Wrist Curl (Barbell)", "ساعد هالتر", ["مچ هالتر", "ساعد از جلو", "مچ دست هالتر"], BB, WR, "forearms", [], ["wrist"]),
    E("reverse_wrist_curl", "Reverse Wrist Curl", "ساعد پشت هالتر", ["مچ برعکس", "ساعد از پشت"], BB, WR, "forearms", [], ["wrist"]),
    E("reverse_curl_barbell", "Reverse Curl (Barbell)", "جلوبازو دست برعکس", ["جلوبازو معکوس", "ساعد جلوبازو برعکس"], BB, WR, "forearms", ["biceps"], ["wrist"]),
    E("farmers_walk", "Farmer's Walk", "راه رفتن کشاورز", ["راه رفتن با دمبل", "فارمر واک", "کشاورز"], DB, DURW, "forearms", ["traps", "abdominals"]),

    # ---------------------------------------------------------------- legs
    E("squat_barbell", "Squat (Barbell)", "اسکوات هالتر", ["اسکوات", "اسکات", "اسکوات از پشت", "اسکات هالتر"], BB, WR, "quadriceps", ["glutes", "hamstrings", "lower_back"], ["knee", "lower_back"]),
    E("front_squat_barbell", "Front Squat (Barbell)", "اسکوات از جلو", ["اسکوات جلو", "فرانت اسکوات"], BB, WR, "quadriceps", ["glutes", "abdominals"], ["knee", "wrist"]),
    E("smith_squat", "Squat (Smith Machine)", "اسکوات اسمیت", ["اسکات اسمیت", "اسکوات دستگاه اسمیت"], MC, WR, "quadriceps", ["glutes"], ["knee"]),
    E("hack_squat", "Hack Squat (Machine)", "هاک اسکوات", ["هاک", "دستگاه هاک", "اسکوات هاک"], MC, WR, "quadriceps", ["glutes"], ["knee"]),
    E("goblet_squat_kettlebell", "Goblet Squat (Kettlebell)", "گابلت اسکوات کتل‌بل", ["گابلت", "اسکوات کتل بل", "گابلت اسکوات"], KB, WR, "quadriceps", ["glutes", "abdominals"], ["knee"]),
    E("goblet_squat_dumbbell", "Goblet Squat (Dumbbell)", "گابلت اسکوات دمبل", ["اسکوات دمبل", "اسکوات جام"], DB, WR, "quadriceps", ["glutes"], ["knee"]),
    E("leg_press", "Leg Press (Machine)", "پرس پا", ["پرس پا دستگاه", "پرس پا ۴۵ درجه", "دستگاه پرس پا"], MC, WR, "quadriceps", ["glutes", "hamstrings"], ["knee", "lower_back"]),
    E("leg_extension", "Leg Extension (Machine)", "جلو پا دستگاه", ["جلوپا", "پا جلو ماشین", "جلو ران دستگاه", "اکستنشن پا"], MC, WR, "quadriceps", [], ["knee"]),
    E("lying_leg_curl", "Lying Leg Curl (Machine)", "پشت پا خوابیده", ["پشت پا دستگاه", "پشت ران خوابیده", "همسترینگ خوابیده"], MC, WR, "hamstrings", ["calves"]),
    E("seated_leg_curl", "Seated Leg Curl (Machine)", "پشت پا نشسته", ["پشت ران نشسته", "همسترینگ نشسته"], MC, WR, "hamstrings", []),
    E("lunge_dumbbell", "Lunge (Dumbbell)", "لانج دمبل", ["لانچ", "لانج", "لانج راه رفتنی", "قیچی"], DB, WR, "quadriceps", ["glutes", "hamstrings"], ["knee"]),
    E("bulgarian_split_squat", "Bulgarian Split Squat", "اسکوات بلغاری", ["بلغاری", "لانج بلغاری", "اسکوات تک پا"], DB, WR, "quadriceps", ["glutes"], ["knee"]),
    E("step_up_dumbbell", "Step Up (Dumbbell)", "استپ‌آپ دمبل", ["بالا رفتن از جعبه", "استپ آپ"], DB, WR, "quadriceps", ["glutes"], ["knee"]),
    E("hip_thrust_barbell", "Hip Thrust (Barbell)", "هیپ تراست هالتر", ["هیپ تراست", "پل باسن هالتر", "باسن هالتر"], BB, WR, "glutes", ["hamstrings"], ["hip"]),
    E("glute_bridge", "Glute Bridge", "پل باسن", ["گلوت بریج", "پل"], BW, REPS, "glutes", ["hamstrings"]),
    E("cable_kickback", "Glute Kickback (Cable)", "باسن سیم‌کش", ["کیک بک باسن", "پا عقب سیمکش", "باسن با سیمکش"], MC, WR, "glutes", ["hamstrings"]),
    E("hip_abduction_machine", "Hip Abduction (Machine)", "دستگاه خارج ران", ["ابداکتور", "خارج ران دستگاه", "باز کردن پا دستگاه"], MC, WR, "abductors_adductors", ["glutes"]),
    E("hip_adduction_machine", "Hip Adduction (Machine)", "دستگاه داخل ران", ["اداکتور", "داخل ران دستگاه", "جمع کردن پا دستگاه"], MC, WR, "abductors_adductors", []),
    E("standing_calf_raise", "Standing Calf Raise (Machine)", "ساق پا ایستاده", ["ساق ایستاده", "ساق دستگاه ایستاده"], MC, WR, "calves", []),
    E("seated_calf_raise", "Seated Calf Raise (Machine)", "ساق پا نشسته", ["ساق نشسته", "ساق دستگاه نشسته"], MC, WR, "calves", []),
    E("calf_press_leg_press", "Calf Press (Leg Press)", "ساق پا با پرس پا", ["ساق پرس پا", "ساق دستگاه پرس"], MC, WR, "calves", []),
    E("sumo_deadlift", "Sumo Deadlift (Barbell)", "ددلیفت سومو", ["سومو", "ددلیفت پا باز"], BB, WR, "glutes", ["quadriceps", "hamstrings", "lower_back", "abductors_adductors"], ["lower_back", "hip"]),
    E("kettlebell_swing", "Kettlebell Swing", "سوئینگ کتل‌بل", ["سوئینگ", "تاب کتل بل"], KB, WR, "glutes", ["hamstrings", "lower_back", "shoulders"], ["lower_back"]),
    E("bodyweight_squat", "Squat (Bodyweight)", "اسکوات وزن بدن", ["اسکوات بدون وزنه", "اسکات آزاد"], BW, REPS, "quadriceps", ["glutes"], ["knee"]),
    E("jump_squat", "Jump Squat", "اسکوات پرشی", ["اسکات پرش", "پرش اسکوات"], BW, REPS, "quadriceps", ["glutes", "calves", "cardio"], ["knee", "ankle"]),

    # ----------------------------------------------------------------- core
    E("crunch", "Crunch", "کرانچ", ["دراز و نشست", "شکم کرانچ", "کرانچ شکم"], BW, REPS, "abdominals", [], ["neck"]),
    E("sit_up", "Sit Up", "دراز و نشست کامل", ["درازنشست", "سیت آپ"], BW, REPS, "abdominals", [], ["lower_back", "neck"]),
    E("cable_crunch", "Cable Crunch", "کرانچ سیم‌کش", ["شکم سیمکش", "کرانچ زانو زده"], MC, WR, "abdominals", []),
    E("hanging_leg_raise", "Hanging Leg Raise", "زیرشکم آویزان", ["بالا آوردن پا آویزان", "زیر شکم بارفیکس", "پا بالا آویزان"], BW, REPS, "abdominals", ["forearms"]),
    E("lying_leg_raise", "Lying Leg Raise", "زیرشکم خوابیده", ["زیر شکم", "پا بالا خوابیده"], BW, REPS, "abdominals", [], ["lower_back"]),
    E("plank", "Plank", "پلانک", ["پلانک شکم", "تخته"], BW, DUR, "abdominals", ["shoulders"]),
    E("side_plank", "Side Plank", "پلانک پهلو", ["پلانک جانبی", "پلانک بغل"], BW, DUR, "abdominals", ["shoulders"]),
    E("russian_twist_plate", "Russian Twist (Plate)", "چرخش روسی با صفحه", ["چرخش روسی", "پهلو صفحه"], PL, WR, "abdominals", []),
    E("ab_wheel", "Ab Wheel Rollout", "چرخ شکم", ["رول اوت", "غلتک شکم"], BW, REPS, "abdominals", ["lats", "shoulders"], ["lower_back"]),
    E("pallof_press_band", "Pallof Press (Band)", "پالوف پرس با کش", ["پالوف", "ضد چرخش کش"], BAND, WR, "abdominals", []),
    E("neck_flexion_plate", "Neck Flexion (Plate)", "گردن جلو با صفحه", ["گردن", "تقویت گردن"], PL, WR, "neck", [], ["neck"]),

    # ------------------------------------------------------------- cardio
    E("treadmill", "Treadmill", "تردمیل", ["دویدن روی تردمیل", "تردمیل دویدن", "پیاده روی تردمیل"], OTH, DISTD, "cardio", ["quadriceps", "calves"], ["knee", "ankle"]),
    E("stationary_bike", "Stationary Bike", "دوچرخه ثابت", ["دوچرخه", "اسپینینگ"], OTH, DISTD, "cardio", ["quadriceps"]),
    E("rowing_machine", "Rowing Machine", "روئینگ (قایقرانی)", ["دستگاه قایقرانی", "روئینگ"], OTH, DISTD, "cardio", ["upper_back", "lats", "quadriceps"]),
    E("elliptical", "Elliptical", "الپتیکال", ["الیپتیکال", "اسکی فضایی"], OTH, DISTD, "cardio", ["quadriceps", "glutes"]),
    E("jump_rope", "Jump Rope", "طناب‌زنی", ["طناب", "طناب زدن"], OTH, DUR, "cardio", ["calves"], ["ankle", "knee"]),
    E("battle_ropes", "Battle Ropes", "طناب بتل", ["بتل روپ", "طناب سنگین"], OTH, DUR, "cardio", ["shoulders", "abdominals"]),
    E("burpee", "Burpee", "برپی", ["بورپی"], BW, REPS, "cardio", ["chest", "quadriceps"], ["wrist", "knee"]),
    E("box_jump", "Box Jump", "پرش روی جعبه", ["پرش جعبه", "باکس جامپ", "پرش جفت"], BW, REPS, "quadriceps", ["glutes", "calves", "cardio"], ["knee", "ankle"]),
    E("sled_push", "Sled Push", "هل دادن سورتمه", ["سورتمه", "اسلد"], OTH, WDIST, "quadriceps", ["glutes", "calves", "cardio"], ["knee"]),
    E("running", "Running", "دویدن", ["دو", "دویدن در فضای باز"], OTH, DISTD, "cardio", ["quadriceps", "calves", "hamstrings"], ["knee", "ankle"]),
]
