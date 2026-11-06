"""Importer helpers for free-exercise-db (https://github.com/yuhonas/free-exercise-db).

The dataset is released into the public domain (Unlicense), images included.
It is English-only, so Persian titles are composed from a glossary of gym
terms in Persian word order: movement, variation, equipment, posture.
Names the glossary cannot compose come from OVERRIDES.
"""
import re

from .taxonomy import Equipment, Muscle, TrackingType

EQUIPMENT_MAP = {
    "barbell": Equipment.BARBELL,
    "e-z curl bar": Equipment.BARBELL,
    "dumbbell": Equipment.DUMBBELL,
    "cable": Equipment.MACHINE,
    "machine": Equipment.MACHINE,
    "kettlebells": Equipment.KETTLEBELL,
    "bands": Equipment.RESISTANCE_BAND,
    "body only": Equipment.REPS_ONLY,
    "medicine ball": Equipment.OTHER,
    "exercise ball": Equipment.OTHER,
    "foam roll": Equipment.OTHER,
    "other": Equipment.OTHER,
    None: Equipment.OTHER,
}

MUSCLE_MAP = {
    "abdominals": Muscle.ABDOMINALS, "abductors": Muscle.ABDUCTORS_ADDUCTORS, "adductors": Muscle.ABDUCTORS_ADDUCTORS,
    "biceps": Muscle.BICEPS, "calves": Muscle.CALVES, "chest": Muscle.CHEST, "forearms": Muscle.FOREARMS,
    "glutes": Muscle.GLUTES, "hamstrings": Muscle.HAMSTRINGS, "lats": Muscle.LATS, "lower back": Muscle.LOWER_BACK,
    "middle back": Muscle.UPPER_BACK, "neck": Muscle.NECK, "quadriceps": Muscle.QUADRICEPS,
    "shoulders": Muscle.SHOULDERS, "traps": Muscle.TRAPS, "triceps": Muscle.TRICEPS,
}

# Persian title of a dataset exercise that already exists in our curated bank.
# Curated rows keep their Persian names and aliases and gain the images.
CURATED = {
    "Barbell Bench Press - Medium Grip": "bench_press_barbell",
    "Barbell Incline Bench Press - Medium Grip": "incline_bench_press_barbell",
    "Decline Barbell Bench Press": "decline_bench_press_barbell",
    "Dumbbell Bench Press": "bench_press_dumbbell",
    "Incline Dumbbell Press": "incline_press_dumbbell",
    "Dumbbell Flyes": "chest_fly_dumbbell",
    "Incline Dumbbell Flyes": "incline_fly_dumbbell",
    "Cable Crossover": "cable_crossover",
    "Butterfly": "chest_fly_machine",
    "Machine Bench Press": "chest_press_machine",
    "Smith Machine Bench Press": "smith_bench_press",
    "Pushups": "push_up",
    "Dips - Chest Version": "chest_dip",
    "Bent-Arm Dumbbell Pullover": "pullover_dumbbell",
    "Barbell Deadlift": "deadlift_barbell",
    "Romanian Deadlift": "romanian_deadlift_barbell",
    "Bent Over Barbell Row": "bent_over_row_barbell",
    "T-Bar Row with Handle": "t_bar_row",
    "One-Arm Dumbbell Row": "dumbbell_row",
    "Wide-Grip Lat Pulldown": "lat_pulldown_cable",
    "Close-Grip Front Lat Pulldown": "lat_pulldown_close_grip",
    "Underhand Cable Pulldowns": "lat_pulldown_reverse_grip",
    "Wide-Grip Pulldown Behind The Neck": "behind_neck_pulldown",
    "Seated Cable Rows": "seated_cable_row",
    "Straight-Arm Pulldown": "straight_arm_pulldown",
    "Pullups": "pull_up",
    "Chin-Up": "chin_up",
    "Weighted Pull Ups": "weighted_pull_up",
    "Hyperextensions (Back Extensions)": "hyperextension",
    "Good Morning": "good_morning_barbell",
    "Barbell Shrug": "shrug_barbell",
    "Dumbbell Shrug": "shrug_dumbbell",
    "Rack Pulls": "rack_pull",
    "Standing Military Press": "overhead_press_barbell",
    "Seated Dumbbell Press": "seated_shoulder_press_dumbbell",
    "Arnold Dumbbell Press": "arnold_press",
    "Machine Shoulder (Military) Press": "shoulder_press_machine",
    "Side Lateral Raise": "lateral_raise_dumbbell",
    "Cable Seated Lateral Raise": "lateral_raise_cable",
    "Front Dumbbell Raise": "front_raise_dumbbell",
    "Front Plate Raise": "front_raise_plate",
    "Seated Bent-Over Rear Delt Raise": "rear_delt_fly_dumbbell",
    "Reverse Machine Flyes": "reverse_fly_machine",
    "Face Pull": "face_pull_cable",
    "Upright Barbell Row": "upright_row_barbell",
    "Barbell Curl": "bicep_curl_barbell",
    "EZ-Bar Curl": "ez_bar_curl",
    "Dumbbell Bicep Curl": "bicep_curl_dumbbell",
    "Hammer Curls": "hammer_curl_dumbbell",
    "Preacher Curl": "preacher_curl",
    "Machine Preacher Curls": "preacher_curl_machine",
    "Concentration Curls": "concentration_curl",
    "Incline Dumbbell Curl": "incline_curl_dumbbell",
    "Standing Biceps Cable Curl": "cable_curl",
    "Triceps Pushdown": "triceps_pushdown_cable",
    "Triceps Pushdown - Rope Attachment": "triceps_rope_pushdown",
    "EZ-Bar Skullcrusher": "skull_crusher_ez",
    "Standing Dumbbell Triceps Extension": "overhead_triceps_extension_dumbbell",
    "Cable Rope Overhead Triceps Extension": "overhead_triceps_extension_cable",
    "Tricep Dumbbell Kickback": "triceps_kickback_dumbbell",
    "Close-Grip Barbell Bench Press": "close_grip_bench_press",
    "Dips - Triceps Version": "triceps_dip",
    "Bench Dips": "bench_dip",
    "Push-Ups - Close Triceps Position": "diamond_push_up",
    "Palms-Up Barbell Wrist Curl Over A Bench": "wrist_curl_barbell",
    "Palms-Down Wrist Curl Over A Bench": "reverse_wrist_curl",
    "Reverse Barbell Curl": "reverse_curl_barbell",
    "Farmer's Walk": "farmers_walk",
    "Barbell Full Squat": "squat_barbell",
    "Front Barbell Squat": "front_squat_barbell",
    "Smith Machine Squat": "smith_squat",
    "Hack Squat": "hack_squat",
    "Goblet Squat": "goblet_squat_kettlebell",
    "Leg Press": "leg_press",
    "Leg Extensions": "leg_extension",
    "Lying Leg Curls": "lying_leg_curl",
    "Seated Leg Curl": "seated_leg_curl",
    "Dumbbell Lunges": "lunge_dumbbell",
    "Split Squat with Dumbbells": "bulgarian_split_squat",
    "Dumbbell Step Ups": "step_up_dumbbell",
    "Barbell Hip Thrust": "hip_thrust_barbell",
    "Butt Lift (Bridge)": "glute_bridge",
    "Glute Kickback": "cable_kickback",
    "Thigh Abductor": "hip_abduction_machine",
    "Thigh Adductor": "hip_adduction_machine",
    "Standing Calf Raises": "standing_calf_raise",
    "Seated Calf Raise": "seated_calf_raise",
    "Calf Press On The Leg Press Machine": "calf_press_leg_press",
    "Sumo Deadlift": "sumo_deadlift",
    "One-Arm Kettlebell Swings": "kettlebell_swing",
    "Bodyweight Squat": "bodyweight_squat",
    "Freehand Jump Squat": "jump_squat",
    "Crunches": "crunch",
    "Sit-Up": "sit_up",
    "Cable Crunch": "cable_crunch",
    "Hanging Leg Raise": "hanging_leg_raise",
    "Flat Bench Lying Leg Raise": "lying_leg_raise",
    "Plank": "plank",
    "Russian Twist": "russian_twist_plate",
    "Ab Roller": "ab_wheel",
    "Pallof Press": "pallof_press_band",
    "Jogging, Treadmill": "treadmill",
    "Bicycling, Stationary": "stationary_bike",
    "Rowing, Stationary": "rowing_machine",
    "Elliptical Trainer": "elliptical",
    "Rope Jumping": "jump_rope",
    "Battling Ropes": "battle_ropes",
    "Front Box Jump": "box_jump",
    "Sled Push": "sled_push",
    "Running, Treadmill": "running",
}

# --- glossary ---------------------------------------------------------------
# (pattern, persian). Patterns are matched on the lower-cased name, longest first.
MOVES = [
    (r"stretch", "کشش"),
    (r"shrug", "کول"), (r"lateral.*jump|jump.*lateral", "پرش جانبی"), (r"side lunge|lateral lunge", "لانج جانبی"),
    (r"reverse crunch", "کرانچ معکوس"), (r"external rotation", "چرخش شانه به بیرون"), (r"internal rotation", "چرخش شانه به داخل"),
    (r"bench press", "پرس سینه"), (r"floor press", "پرس سینه روی زمین"), (r"chest press", "پرس سینه"),
    (r"military press|shoulder press|overhead press|push press", "پرس سرشانه"), (r"arnold", "پرس آرنولد"),
    (r"leg press", "پرس پا"), (r"calf press", "ساق پا پرس"), (r"jm press", "جی‌ام پرس پشت بازو"),
    (r"incline .*press|press.* incline", "پرس بالاسینه"), (r"decline .*press", "پرس زیرسینه"),
    (r"landmine", "لندماین"), (r"pallof", "پالوف پرس"), (r"\bpress\b", "پرس"),
    (r"skull ?crusher|lying triceps|french press", "پشت بازو خوابیده"),
    (r"pushdown|push-down", "پشت بازو سیم‌کش"), (r"kickback", "کیک‌بک"),
    (r"triceps? extension|tricep", "پشت بازو"),
    (r"leg extension", "جلو پا"), (r"leg curl|hamstring curl", "پشت پا"), (r"wrist curl|wrist roller", "ساعد"),
    (r"preacher", "جلوبازو لاری"), (r"hammer", "جلوبازو چکشی"), (r"concentration", "جلوبازو تمرکزی"),
    (r"zottman", "جلوبازو زاتمن"), (r"reverse.*curl", "جلوبازو دست برعکس"), (r"curl", "جلوبازو"),
    (r"calf raise|calf", "ساق پا"), (r"lateral raise|side lateral|laterals|lateral", "نشر از جانب"),
    (r"front raise|front .*raise", "نشر از جلو"), (r"rear delt|reverse fly|reverse flye|bent.over.*raise", "نشر خم"),
    (r"leg raise|knee raise|knee tuck|tuck", "زیرشکم"), (r"raise", "نشر"),
    (r"upright row", "کول از جلو (اپرایت رو)"), (r"t-bar", "زیربغل تی‌بار"), (r"seated cable row|cable row", "زیربغل قایقی"),
    (r"inverted row", "زیربغل معکوس"), (r"\brows?\b|rowing", "زیربغل"),
    (r"pulldown|pull-down", "لت سیم‌کش"), (r"pullover", "پلاور"), (r"face pull", "فیس‌پول"),
    (r"chin.?up|chins", "بارفیکس دست برعکس"), (r"pull.?ups?|pullups", "بارفیکس"), (r"muscle up", "ماسل‌آپ"),
    (r"romanian|stiff.legged|stiff leg", "ددلیفت رومانیایی"), (r"sumo deadlift", "ددلیفت سومو"),
    (r"deadlift", "ددلیفت"), (r"rack pull", "رک پول"), (r"good morning", "گودمورنینگ"),
    (r"hyperextension|back extension", "فیله کمر"), (r"superman", "سوپرمن"),
    (r"split squat", "اسکوات بلغاری"), (r"front squat", "اسکوات از جلو"), (r"hack squat", "هاک اسکوات"),
    (r"goblet", "گابلت اسکوات"), (r"pistol", "اسکوات تک‌پا (پیستول)"), (r"jump squat|squat jump", "اسکوات پرشی"),
    (r"sissy squat", "سیسی اسکوات"), (r"squat", "اسکوات"), (r"lunge", "لانج"), (r"step.?up", "استپ‌آپ"),
    (r"hip thrust", "هیپ تراست"), (r"bridge|butt lift", "پل باسن"), (r"glute", "باسن"),
    (r"abductor|abduction", "خارج ران"), (r"adductor|adduction", "داخل ران"),
    (r"shrug", "کول"), (r"fly|flye|flyes", "قفسه سینه"), (r"crossover", "کراس‌اوور"), (r"butterfly", "قفسه دستگاه"),
    (r"push.?ups?|pushups", "شنای سوئدی"), (r"\bdips?\b", "دیپ پارالل"),
    (r"crunch", "کرانچ"), (r"sit.?up", "دراز و نشست"), (r"plank", "پلانک"), (r"russian twist|twist", "چرخش تنه"),
    (r"ab roller|rollout|ab wheel", "چرخ شکم"), (r"oblique", "پهلو"), (r"wood ?chop", "وودچاپ"),
    (r"mountain climber", "کوهنورد"), (r"burpee", "برپی"), (r"jumping jack", "جامپینگ جک"),
    (r"power clean", "پاور کلین"), (r"hang clean", "هنگ کلین"), (r"clean and jerk", "دوضرب"),
    (r"clean and press", "کلین و پرس"), (r"\bclean", "کلین"), (r"snatch", "یک‌ضرب (اسنچ)"), (r"jerk", "جرک"),
    (r"thruster", "تراستر"), (r"swing", "سوئینگ"), (r"turkish get.?up", "ترکیش گت‌آپ"), (r"windmill", "ویندمیل"),
    (r"halo", "هالو"), (r"carry|farmer", "راه رفتن کشاورز"), (r"sled|prowler", "سورتمه"),
    (r"tire flip", "برگرداندن تایر"), (r"atlas stone", "سنگ اطلس"), (r"yoke", "یوک"), (r"log lift", "بلند کردن کنده"),
    (r"keg", "بشکه"), (r"sandbag", "کیسه شن"), (r"sledgehammer", "پتک"),
    (r"box jump|jump.*box", "پرش روی جعبه"), (r"depth jump", "پرش عمقی"), (r"hops?\b|hopping", "لی‌لی"),
    (r"bound", "پرش بلند"), (r"jump", "پرش"), (r"sprint", "دوی سرعت"), (r"skip", "اسکیپ"),
    (r"treadmill", "تردمیل"), (r"bicycl|bike", "دوچرخه ثابت"), (r"elliptical", "الپتیکال"),
    (r"stair", "پله"), (r"jog", "دویدن آرام"), (r"running|run\b", "دویدن"), (r"walk", "راه رفتن"),
    (r"rope jump|jump rope", "طناب‌زنی"), (r"battling rope", "طناب بتل"),
    (r"throw|slam|pass", "پرتاب توپ"), (r"smr|foam roll|roller", "ماساژ با فوم رولر"),
    (r"stretch", "کشش"), (r"rotation", "چرخش"), (r"circles", "چرخش دایره‌ای"),
]

STRETCH_TARGET = [
    (r"hamstring", "همسترینگ"), (r"quad", "چهارسر ران"), (r"calf|calves|gastrocnemius|soleus|achilles", "ساق پا"),
    (r"chest|pec", "سینه"), (r"shoulder|delt", "سرشانه"), (r"triceps|tricep", "پشت بازو"), (r"biceps?", "جلوبازو"),
    (r"lat\b|lats|latissimus", "زیربغل"), (r"hip flexor", "خم‌کننده ران"), (r"groin|adductor", "کشاله ران"),
    (r"glute|piriformis", "باسن"), (r"neck", "گردن"), (r"lower back|spinal", "کمر"), (r"upper back", "پشت"),
    (r"it band|iliotibial", "نوار ایلیوتیبیال"), (r"forearm|wrist", "ساعد"), (r"ankle", "مچ پا"),
    (r"abdominal|stomach", "شکم"),
]

MODIFIERS = [  # variation/grip — placed after the movement
    (r"close.grip|narrow", "دست جمع"), (r"wide.grip|wide", "دست باز"), (r"reverse.grip|underhand|supinated", "دست برعکس"),
    (r"neutral grip", "دست موازی"), (r"one.arm|single.arm|one arm", "تک‌دست"), (r"one.leg|single.leg|one leg", "تک‌پا"),
    (r"alternat", "یک‌درمیان"), (r"behind the neck|behind.neck", "از پشت گردن"), (r"overhead", "از بالای سر"),
    (r"bent.over", "خم"), (r"rear", "از پشت"), (r"isometric", "ایستا"), (r"weighted", "با وزنه"), (r"assisted", "کمکی"),
    (r"pause", "با مکث"), (r"oblique", "پهلو"), (r"scapular", "کتف"), (r"\bpower\b", "پاور"), (r"\bhang\b", "هنگ"), (r"deficit", "از روی سکو"), (r"partial", "نیمه"), (r"rope", "طناب"),
]

POSTURE = [  # placed at the end
    (r"incline", "شیب مثبت"), (r"decline", "شیب منفی"), (r"seated|sitting", "نشسته"), (r"standing", "ایستاده"),
    (r"lying|supine|prone|flat bench", "خوابیده"), (r"kneeling", "زانو زده"), (r"hanging", "آویزان"),
    (r"on (a|an|the)? ?(exercise|stability|swiss) ?ball|physioball", "روی توپ"),
]

EQUIP_FA = [
    (r"smith", "اسمیت"), (r"e-?z|ez.bar|ez bar", "هالتر EZ"), (r"barbell|\bbar\b", "هالتر"), (r"dumbbell|\bdb\b", "دمبل"),
    (r"kettlebell", "کتل‌بل"), (r"cable|pulley", "سیم‌کش"), (r"machine|leverage", "دستگاه"),
    (r"band", "کش"), (r"medicine ball", "توپ مدیسن"), (r"plate", "صفحه"), (r"chain", "زنجیر"),
]

# Exercises whose movement the glossary does not capture well.
OVERRIDES = {
    "3/4 Sit-Up": "دراز و نشست سه‌چهارم",
    "Superman": "سوپرمن",
    "Inchworm": "کرم اندازه‌گیر (اینچ‌ورم)",
    "Bear Crawl Sled Drags": "کشیدن سورتمه با راه رفتن خرسی",
    "Dead Bug": "ددباگ",
    "Bird Dog": "برد داگ",
    "Spider Crawl": "حرکت عنکبوتی",
    "Stomach Vacuum": "واکیوم شکم",
    "Windshield Wipers": "برف‌پاک‌کن",
    "Flutter Kicks": "قیچی پا",
    "Scissor Kick": "قیچی پا",
    "Scissors Jump": "پرش قیچی",
    "Child's Pose": "حالت کودک (کشش)",
    "Cat Stretch": "کشش گربه",
    "World's Greatest Stretch": "کشش ترکیبی کامل بدن",
    "Frankenstein Squat": "اسکوات فرانکنشتاین",
    "Zercher Squats": "اسکوات زرچر",
    "Iron Cross": "صلیب آهنی",
    "Gorilla Chin/Crunch": "بارفیکس گوریلا با کرانچ",
    "Kipping Muscle Up": "ماسل‌آپ کیپینگ",
    "Handstand Push-Ups": "شنای بالانس دست",
    "Rocky Pull-Ups/Pulldowns": "بارفیکس و لت راکی",
    "Bradford/Rocky Presses": "پرس برادفورد",
    "Gironda Sternum Chins": "بارفیکس جیروندا",
    "Svend Press": "پرس سوند",
    "Tate Press": "پرس تیت",
    "Otis-Up": "اوتیس‌آپ",
    "Car Drivers": "فرمان ماشین با صفحه",
    "Mixed Grip Chin": "بارفیکس دست ترکیبی",
    "Star Jump": "پرش ستاره",
    "Frog Hops": "پرش قورباغه",
    "Carioca Quick Step": "کاریوکا",
    "Shotgun Row": "زیربغل تک‌دست سیم‌کش (شات‌گان)",
    "Renegade Row": "زیربغل رنگید",
    "Seesaw Press (Alternating Side Press)": "پرس الاکلنگی",
    "Conan's Wheel": "چرخ کونان",
    "Circus Bell": "سیرکس بل",
    "Rickshaw Carry": "حمل ریکشا",
    "Rickshaw Deadlift": "ددلیفت ریکشا",
    "Spell Caster": "اسپل کستر",
    "Suitcase Crunch": "کرانچ چمدانی",
    "Jackknife Sit-Up": "دراز و نشست چاقویی",
    "Pirate Ships": "کشتی دزدان دریایی",
    "Groiners": "گروینر",
    "Heaving Snatch Balance": "اسنچ بالانس",
    "Hang Snatch": "هنگ اسنچ",
    "Stairmaster": "دستگاه پله",
    "Recumbent Bike": "دوچرخه ثابت نشسته",
    "Trail Running/Walking": "دویدن و پیاده‌روی در طبیعت",
    "Walking, Treadmill": "پیاده‌روی روی تردمیل",
    "Jogging, Treadmill": "دویدن آرام روی تردمیل",
    "90/90 Hamstring": "کشش همسترینگ ۹۰/۹۰",
    "Alternate Heel Touchers": "لمس پاشنه یک‌درمیان (پهلو)",
    "Ankle On The Knee": "کشش باسن مچ روی زانو",
    "Around The Worlds": "دور دنیا با دمبل",
    "Backward Drag": "کشیدن سورتمه رو به عقب",
    "Balance Board": "تخته تعادل",
    "Band Pull Apart": "باز کردن کش از جلو",
    "Barbell Side Bend": "خم جانبی با هالتر",
    "Body-Up": "بادی‌آپ (پلانک به شنا)",
    "Bottoms Up": "زیرشکم باسن به بالا",
    "Butt-Ups": "بالا آوردن باسن در پلانک",
    "Cable Iron Cross": "صلیب آهنی سیم‌کش",
    "Cable Judo Flip": "چرخش جودو سیم‌کش",
    "Chain Handle Extension": "پشت بازو با دستگیره زنجیر",
    "Chest Push from 3 point stance": "پرتاب توپ سینه از حالت سه‌نقطه",
    "Chest Push (multiple response)": "پرتاب توپ سینه پیاپی",
    "Chest Push (single response)": "پرتاب توپ سینه تکی",
    "Cocoons": "پیله (شکم)",
    "Cross Over - With Bands": "کراس‌اوور با کش",
    "Crucifix": "نگه‌داشتن صلیبی وزنه",
    "Double Leg Butt Kick": "پرش دوپا پاشنه به باسن",
    "Downward Facing Balance": "تعادل رو به پایین روی توپ",
    "Drop Push": "شنای افتادنی",
    "Dumbbell Lying Pronation": "چرخش ساعد به داخل خوابیده دمبل",
    "Dumbbell Lying Supination": "چرخش ساعد به بیرون خوابیده دمبل",
    "Dumbbell Scaption": "نشر اسکپشن دمبل",
    "Dumbbell Side Bend": "خم جانبی با دمبل",
    "Elbow to Knee": "کرانچ آرنج به زانو",
    "Elbows Back": "کشش سینه آرنج به عقب",
    "Exercise Ball Pull-In": "جمع کردن زانو روی توپ",
    "Flat Bench Leg Pull-In": "جمع کردن پا روی نیمکت",
    "Hanging Pike": "پایک آویزان",
    "Heavy Bag Thrust": "ضربه به کیسه سنگین",
    "Hip Extension with Bands": "باز کردن ران با کش",
    "Hip Flexion with Band": "خم کردن ران با کش",
    "Hip Lift with Band": "بالا آوردن لگن با کش",
    "Hug A Ball": "کشش کمر با بغل کردن توپ",
    "Hug Knees To Chest": "کشش کمر زانو به سینه",
    "Incline Bench Pull": "زیربغل روی نیمکت شیب‌دار",
    "Incline Dumbbell Bench With Palms Facing In": "پرس بالاسینه دمبل دست موازی",
    "Isometric Chest Squeezes": "فشار ایستای سینه",
    "Isometric Neck Exercise - Front And Back": "گردن ایستا جلو و عقب",
    "Isometric Neck Exercise - Sides": "گردن ایستا جانبی",
    "Isometric Wipers": "برف‌پاک‌کن ایستا",
    "Kettlebell Figure 8": "عدد ۸ با کتل‌بل",
    "Kettlebell Pirate Ships": "کشتی دزدان دریایی با کتل‌بل",
    "Kettlebell Sumo High Pull": "کشش بالای سومو کتل‌بل",
    "Knee Across The Body": "کشش باسن زانو روی بدن",
    "Kneeling Arm Drill": "تمرین حرکت دست زانو زده",
    "Kneeling Hip Flexor": "کشش خم‌کننده ران زانو زده",
    "Leg Lift": "بالا آوردن پا",
    "Leg Pull-In": "جمع کردن پا",
    "Linear 3-Part Start Technique": "تکنیک استارت سه‌مرحله‌ای",
    "Linear Acceleration Wall Drill": "تمرین شتاب با دیوار",
    "Looking At Ceiling": "کشش گردن نگاه به سقف",
    "Lying Bent Leg Groin": "کشش کشاله ران خوابیده",
    "Lying Face Down Plate Neck Resistance": "گردن با صفحه خوابیده رو به پایین",
    "Lying Face Up Plate Neck Resistance": "گردن با صفحه خوابیده رو به بالا",
    "Lying Hamstring": "کشش همسترینگ خوابیده",
    "Lying Prone Quadriceps": "کشش چهارسر خوابیده",
    "Moving Claw Series": "تمرین پنجه دویدن",
    "One-Arm High-Pulley Cable Side Bends": "خم جانبی تک‌دست سیم‌کش",
    "One Arm Against Wall": "کشش زیربغل تک‌دست به دیوار",
    "One Half Locust": "ملخ نیمه (کمر)",
    "One Handed Hang": "آویزان تک‌دست",
    "One Knee To Chest": "کشش تک‌زانو به سینه",
    "Overhead Lat": "کشش زیربغل از بالای سر",
    "Pin Presses": "پرس سینه از روی پین",
    "Plate Pinch": "نگه‌داشتن صفحه با انگشت",
    "Platform Hamstring Slides": "سرشی همسترینگ روی سکو",
    "Power Partials": "نشر نیمه انفجاری",
    "Prone Manual Hamstring": "پشت پا با مقاومت یار",
    "Pull Through": "پول‌ترو سیم‌کش",
    "Pyramid": "کشش هرمی",
    "Quick Leap": "جهش سریع",
    "Rack Delivery": "تحویل هالتر به رک (کلین)",
    "Return Push from Stance": "پرتاب برگشتی از حالت ایستاده",
    "Rope Climb": "طناب‌نوردی",
    "Seated Biceps": "کشش جلوبازو نشسته",
    "Seated Flat Bench Leg Pull-In": "جمع کردن پا نشسته روی نیمکت",
    "Seated Front Deltoid": "کشش سرشانه جلو نشسته",
    "Seated Hamstring": "کشش همسترینگ نشسته",
    "Seated Head Harness Neck Resistance": "گردن با هدبند وزنه نشسته",
    "Side Jackknife": "چاقوی جانبی (پهلو)",
    "Side Wrist Pull": "کشش مچ جانبی",
    "Side to Side Box Shuffle": "جابه‌جایی جانبی روی جعبه",
    "Single-Arm Linear Jammer": "جمر تک‌دست",
    "Single Leg Butt Kick": "پاشنه به باسن تک‌پا",
    "Single Leg Push-off": "هل دادن تک‌پا از جعبه",
    "Skating": "اسکیت (پرش جانبی)",
    "Standing Cable Lift": "بالا کشیدن مورب سیم‌کش",
    "Standing Hip Flexors": "کشش خم‌کننده ران ایستاده",
    "Standing Olympic Plate Hand Squeeze": "فشار صفحه با دست",
    "Standing Pelvic Tilt": "تیلت لگن ایستاده",
    "Standing Toe Touches": "لمس پنجه ایستاده",
    "Step Mill": "دستگاه پله برقی",
    "Suspended Fallout": "فال‌اوت با بند معلق",
    "The Straddle": "کشش پای باز",
    "Toe Touchers": "لمس پنجه خوابیده (شکم)",
    "Upper Back-Leg Grab": "کشش پشت با گرفتن پا",
    "Weighted Ball Side Bend": "خم جانبی با توپ وزنه",
}

_STOP = set("with the a an on of to and in from for at into off over through your".split())


def _find(pats, s):
    for pat, fa in pats:
        if re.search(pat, s):
            return fa
    return None


def _find_all(pats, s):
    seen = []
    for pat, fa in pats:
        if re.search(pat, s) and fa not in seen:
            seen.append(fa)
    return seen


def persian_title(name: str, primary: str | None = None) -> tuple[str, bool]:
    """Return (persian title, confident)."""
    if name in OVERRIDES:
        return OVERRIDES[name], True
    s = name.lower().replace("_", " ")
    move = _find(MOVES, s)
    if move is None:
        return name, False
    parts = [move]
    if move == "کشش":
        target = _find(STRETCH_TARGET, s)
        if target:
            parts.append(target)
    for m in _find_all(MODIFIERS, s):
        if m not in move:
            parts.append(m)
    eq = _find(EQUIP_FA, s)
    if eq and eq not in move:
        parts.append(eq)
    for p in _find_all(POSTURE, s):
        if p not in move and not (p == "شیب مثبت" and "بالاسینه" in move) and not (p == "شیب منفی" and "زیرسینه" in move):
            parts.append(p)
    return " ".join(parts), True


def tracking_for(ex: dict, equipment: str) -> str:
    cat, force, name = ex.get("category"), ex.get("force"), ex["name"].lower()
    if cat == "cardio":
        return TrackingType.DURATION if re.search(r"rope|jump", name) else TrackingType.DISTANCE_DURATION
    if cat == "stretching" or "smr" in name:
        return TrackingType.DURATION
    if re.search(r"sled|prowler|yoke|carry|farmer|walk", name):
        return TrackingType.WEIGHT_DISTANCE if "farmer" not in name else TrackingType.DURATION_WEIGHT
    if force == "static" or "plank" in name or "isometric" in name:
        return TrackingType.DURATION
    if equipment == Equipment.REPS_ONLY:
        if re.search(r"pull.?up|chin|dip", name):
            return TrackingType.BODYWEIGHT_REPS
        return TrackingType.REPS_ONLY
    return TrackingType.WEIGHT_REPS


INJURY_RULES = [
    (r"squat|lunge|leg press|leg extension|jump|hop|bound|step.?up|pistol|sprint", "knee"),
    (r"deadlift|good morning|bent over.*row|hyperextension|back extension|clean|snatch|jerk|swing|stone|tire|keg", "lower_back"),
    (r"overhead|military|shoulder press|behind.*neck|upright row|dip|snatch|jerk|handstand|bench press", "shoulder"),
    (r"skull|lying triceps|french|triceps extension|jm press|tate", "elbow"),
    (r"wrist|push.?up|front squat|clean", "wrist"),
    (r"neck|shrug", "neck"),
]


def injuries_for(name: str) -> list[str]:
    s = name.lower()
    out = []
    for pat, tag in INJURY_RULES:
        if re.search(pat, s) and tag not in out:
            out.append(tag)
    return out


def slug_for(ex_id: str) -> str:
    return "fedb_" + re.sub(r"[^a-z0-9]+", "_", ex_id.lower()).strip("_")[:70]


# Words that tell two same-named variations apart ("Box Squat" vs "Chair Squat").
QUALIFIERS = {
    "box": "روی جعبه", "chair": "با صندلی", "olympic": "المپیکی", "jefferson": "جفرسون", "jerk": "جرک",
    "sit": "نشسته", "board": "با تخته", "bent": "خم", "cuban": "کوبایی", "clean": "کلین", "anti": "ضدجاذبه",
    "clock": "ساعتی", "plyo": "پلایومتریک", "elevated": "پا بالا", "suspended": "با بند تی‌آر‌ایکس", "plank": "تا پلانک",
    "ankle": "مچ پا", "arm": "بازو", "elbow": "آرنج", "knee": "زانو", "shoulder": "شانه", "wrist": "مچ دست", "neck": "گردن",
    "muscle": "ماسل", "balance": "بالانس", "pull": "پول", "blocks": "از روی بلوک", "split": "اسپلیت", "hang": "از آویزان",
    "power": "پاور", "crossover": "ضربدری", "reverse": "معکوس", "walking": "راه‌رونده", "pass": "پاس", "sprint": "دوی سرعت",
    "all": "چهاردست‌وپا", "fours": "", "back": "به پشت", "side": "از پهلو", "flexor": "خم‌کننده لگن", "dynamic": "پویا",
    "behind": "پشت سر", "head": "", "chin": "چانه", "front": "جلو", "axle": "میله ضخیم", "car": "ماشین",
    "drag": "درگ", "finger": "انگشت", "spider": "اسپایدر", "lower": "پایین", "tuck": "جمع", "jump": "پرش",
    "step": "استپ", "london": "لندنی", "pelvic": "تیلت لگن", "bands": "با کش", "band": "با کش", "dumbbell": "دمبل",
    "plie": "پلیه", "bodyweight": "وزن بدن", "mid": "میانی", "sled": "سورتمه", "air": "ایربایک", "bicycling": "دوچرخه‌سواری",
    "cone": "مخروط", "wind": "باد", "bench": "نیمکت", "stiff": "پا صاف", "good": "گودمورنینگ", "smr": "",
    "anterior": "ساق جلو", "tibialis": "", "brachialis": "بازویی", "calves": "ساق", "foot": "کف پا", "hamstring": "همسترینگ",
    "iliotibial": "نوار ایلیوتیبیال", "latissimus": "زیربغل", "piriformis": "پیریفورمیس", "quadriceps": "چهارسر",
    "rhomboids": "رومبوئید", "peroneals": "نازک‌نئی", "adductor": "نزدیک‌کننده", "groin": "کشاله", "chest": "سینه",
    "middle": "وسط", "upper": "بالا", "dancer": "رقصنده", "iron": "صلیب آهنی", "intermediate": "متوسط", "lying": "خوابیده",
    "seated": "نشسته", "standing": "ایستاده", "kneeling": "زانو زده", "single": "تک", "one": "تک", "two": "دو",
    "incline": "شیب مثبت", "decline": "شیب منفی", "close": "دست جمع", "wide": "دست باز", "grip": "", "palms": "کف دست",
    "hammer": "چکشی", "zottman": "زوتمن", "preacher": "لاری", "cable": "سیم‌کش", "machine": "دستگاه", "kettlebell": "کتل‌بل",
    "barbell": "هالتر", "smith": "اسمیت", "leverage": "اهرمی", "ball": "توپ", "medicine": "مدیسن‌بال", "floor": "روی زمین",
    "overhead": "بالای سر", "high": "بالا", "low": "پایین", "speed": "سرعتی", "chains": "با زنجیر", "double": "دوبل",
    "landmine": "لندماین", "atlas": "اطلس", "inverted": "معکوس", "hops": "پرش کوتاه", "depth": "عمقی", "throw": "پرتاب",
    "windmill": "آسیاب بادی", "rollout": "رول‌اوت", "external": "خارجی", "rotation": "چرخش", "oblique": "مورب",
    "military": "سرشانه نظامی", "extension": "اکستنشن", "triceps": "پشت بازو", "tricep": "پشت بازو", "curl": "جلوبازو",
    "row": "قایقی", "shrug": "شراگ", "raise": "بالا آوردن", "crunch": "کرانچ", "lunge": "لانج", "squat": "اسکوات",
    "glute": "باسن", "hip": "لگن", "calf": "ساق", "leg": "پا", "body": "بدن", "parallel": "پارالل", "natural": "طبیعی",
    "pronated": "دست رو", "straight": "صاف", "bosu": "بوسو", "runner": "دونده", "posterior": "پشتی", "elbows": "آرنج",
    "gastrocnemius": "دوقلو", "soleus": "نعلی", "achilles": "آشیل", "round": "گرد", "world": "جهان", "spinal": "ستون فقرات",
    "rocking": "تابی", "frog": "قورباغه", "janda": "یاندا", "trap": "ذوزنقه‌ای", "romanian": "رومانیایی", "fast": "سریع",
    "skipping": "اسکیپ", "skip": "اسکیپ", "release": "رهاسازی", "iso": "ایزومتریک", "upright": "ایستاده", "stone": "سنگ",
    "stones": "سنگ", "prowler": "پراولر", "harness": "با هارنس", "flutter": "قیچی", "scissor": "قیچی", "jammer": "جمر",
    "laterals": "جانبی", "lateral": "جانبی", "catch": "گرفتن", "slam": "کوبیدن", "backward": "رو به عقب", "scoop": "اسکوپ",
    "forward": "رو به جلو", "guillotine": "گیوتین", "rocket": "راکت", "leap": "جهش", "bound": "بوند", "hurdle": "مانع",
    "linear": "خطی", "trainer": "ترینر", "open": "باز", "against": "", "wall": "روی دیوار", "extended": "کشیده",
}


def disambiguate(title_fa: str, title_en: str) -> str:
    """Add the words that set this variation apart; keep the English name as a last resort."""
    extra = []
    for tok in re.findall(r"[a-z]+", title_en.lower()):
        q = QUALIFIERS.get(tok)
        if q and q not in title_fa and q not in extra:
            extra.append(q)
    return " ".join([title_fa, *extra])
