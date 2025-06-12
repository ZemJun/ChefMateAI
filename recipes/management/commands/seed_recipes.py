# recipes/management/commands/seed_recipes.py (优化版)

import random
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, RecipeIngredient, RecipeStep, Review

User = get_user_model()

RECIPES_DATA = [
    {
        'recipe': {
            'title': '番茄炒蛋',
            'description': '一道家喻户晓的国民家常菜，酸甜开胃，营养丰富，制作简单快速，是厨房新手的入门首选。',
            'cooking_time_minutes': 15,
            'difficulty': 1,
            'cuisine_type': '家常菜',
            'status': 'published',
        },
        'author_username': 'admin',
        'ingredients': [
            {'name': '番茄', 'quantity': 2, 'unit': 'piece', 'notes': '切块'},
            {'name': '鸡蛋', 'quantity': 3, 'unit': 'piece', 'notes': '打散'},
            {'name': '葱', 'quantity': 10, 'unit': 'g', 'notes': '切葱花'},
            {'name': '大蒜', 'quantity': 2, 'unit': 'piece', 'notes': '切末'},
            {'name': '白砂糖', 'quantity': 1, 'unit': 'tsp', 'notes': '可选，中和酸味'},
            {'name': '食盐', 'quantity': 0.5, 'unit': 'tsp', 'notes': '或适量'},
            {'name': '花生油', 'quantity': 2, 'unit': 'tbsp'},
        ],
        'steps': [
            '将番茄洗净，顶部划十字，用开水烫一下去皮，然后切成小块。',
            '鸡蛋打入碗中，加少许盐搅打均匀。小葱切成葱花，大蒜切末。',
            '热锅倒油，油热后倒入蛋液，用筷子快速划散，炒至金黄凝固后盛出备用。',
            '锅中留底油，放入蒜末爆香，然后倒入番茄块，中火翻炒至软烂出汁。',
            '加入一茶匙白砂糖和适量盐翻炒均匀，中和番茄的酸味。',
            '倒入之前炒好的鸡蛋，快速翻炒均匀，让鸡蛋吸满番茄的汤汁。',
            '出锅前撒上葱花点缀即可。'
        ]
    },
    {
        'recipe': {
            'title': '可乐鸡翅',
            'description': '一道广受欢迎的甜咸口味菜肴，用可乐代替糖色，做法简单，成品色泽红亮，味道鲜美，深受孩子和年轻人的喜爱。',
            'cooking_time_minutes': 30,
            'difficulty': 1,
            'cuisine_type': '家常菜',
            'status': 'published',
        },
        'author_username': 'admin',
        'ingredients': [
            {'name': '鸡翅', 'quantity': 10, 'unit': 'piece', 'notes': '中翅为佳，两面划几刀'},
            {'name': '可乐', 'quantity': 500, 'unit': 'ml', 'notes': '一罐普通可乐即可'},
            {'name': '生姜', 'quantity': 3, 'unit': 'slice'},
            {'name': '大葱', 'quantity': 1, 'unit': 'piece', 'notes': '切段'},
            {'name': '料酒', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '酱油', 'quantity': 2, 'unit': 'tbsp'},
            {'name': '食盐', 'quantity': 0.5, 'unit': 'tsp'},
        ],
        'steps': [
            '鸡翅洗净，在两面用刀划几道口子，方便入味。',
            '冷水下锅，放入鸡翅、姜片和料酒，大火煮开焯水，撇去浮沫后捞出冲洗干净。',
            '热锅少油，放入鸡翅，小火煎至两面金黄。',
            '倒入可乐，没过鸡翅即可。加入酱油、葱段。',
            '大火烧开后，转小火慢炖20分钟左右。',
            '开大火收汁，待汤汁浓稠包裹在鸡翅上即可出锅。',
            '出锅后可以撒上一些白芝麻点缀。'
        ]
    },
    {
        'recipe': {
            'title': '红烧牛肉',
            'description': '经典的中华名菜，牛肉软烂入味，汤汁浓郁醇厚，无论是配米饭还是面条都是绝佳选择。',
            'cooking_time_minutes': 90,
            'difficulty': 2,
            'cuisine_type': '家常菜',
            'status': 'published',
        },
        'author_username': 'admin',
        'ingredients': [
            {'name': '牛腩', 'quantity': 500, 'unit': 'g', 'notes': '切成3cm左右的块'},
            {'name': '胡萝卜', 'quantity': 1, 'unit': 'piece', 'notes': '切滚刀块'},
            {'name': '土豆', 'quantity': 1, 'unit': 'piece', 'notes': '切滚刀块'},
            {'name': '生姜', 'quantity': 5, 'unit': 'slice'},
            {'name': '大葱', 'quantity': 2, 'unit': 'piece', 'notes': '切段'},
            {'name': '八角', 'quantity': 2, 'unit': 'piece'},
            {'name': '桂皮', 'quantity': 1, 'unit': 'piece', 'notes': '小块'},
            {'name': '干辣椒', 'quantity': 3, 'unit': 'piece', 'notes': '可选'},
            {'name': '酱油', 'quantity': 3, 'unit': 'tbsp'},
            {'name': '料酒', 'quantity': 2, 'unit': 'tbsp'},
            {'name': '冰糖', 'quantity': 20, 'unit': 'g'},
        ],
        'steps': [
            '牛腩切块，冷水下锅，加入姜片和料酒焯水，煮沸后捞出洗净。',
            '热锅热油，放入冰糖，小火炒出糖色（呈焦糖色）。',
            '迅速倒入焯好水的牛腩块，翻炒均匀，使每块牛肉都裹上糖色。',
            '加入姜片、葱段、八角、桂皮、干辣椒，翻炒出香味。',
            '烹入料酒，加入酱油，翻炒均匀。',
            '加入足量开水，没过牛肉。大火烧开后转小火，加盖慢炖60分钟。',
            '加入切好的胡萝卜块和土豆块，继续炖煮20-30分钟，直到所有食材软烂。',
            '最后根据口味加入适量盐调味，大火收汁至汤汁浓稠即可。'
        ]
    },
    {
        'recipe': {
            'title': '蒜蓉西兰花',
            'description': '一道健康快手的素菜，最大程度保留了西兰花的营养和爽脆口感，蒜香浓郁，清淡美味。',
            'cooking_time_minutes': 10,
            'difficulty': 1,
            'cuisine_type': '家常菜',
            'status': 'published',
        },
        'author_username': 'admin',
        'ingredients': [
            {'name': '西兰花', 'quantity': 1, 'unit': 'piece', 'notes': '掰成小朵'},
            {'name': '大蒜', 'quantity': 5, 'unit': 'piece', 'notes': '切成蒜蓉'},
            {'name': '蚝油', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '食盐', 'quantity': 0.5, 'unit': 'tsp'},
            {'name': '淀粉', 'quantity': 1, 'unit': 'tsp', 'notes': '用于勾芡'},
            {'name': '花生油', 'quantity': 1, 'unit': 'tbsp'},
        ],
        'steps': [
            '西兰花掰成小朵，用盐水浸泡10分钟，然后冲洗干净。',
            '大蒜切成蒜蓉备用。淀粉加少量水调成水淀粉。',
            '烧一锅开水，加入少许盐和几滴油，放入西兰花焯水约1分钟，捞出沥干。',
            '热锅冷油，放入一半蒜蓉，小火炒出香味。',
            '倒入焯好水的西兰花，大火快速翻炒。',
            '加入蚝油、盐，翻炒均匀。',
            '淋入水淀粉勾薄芡，出锅前撒上剩下的一半蒜蓉，翻拌均匀即可。'
        ]
    },
    {
        'recipe': {
            'title': '香煎三文鱼配柠檬黄油汁',
            'description': '经典的西式做法，外皮香脆，鱼肉鲜嫩多汁。搭配酸爽的柠檬黄油汁，既能解腻又能提升风味，是一道高雅又简单的快手菜。',
            'cooking_time_minutes': 20,
            'difficulty': 2,
            'cuisine_type': '西餐',
            'status': 'published',
        },
        'author_username': 'admin',
        'ingredients': [
            {'name': '三文鱼', 'quantity': 200, 'unit': 'g', 'notes': '带皮鱼排'},
            {'name': '柠檬', 'quantity': 1, 'unit': 'piece'},
            {'name': '黄油', 'quantity': 30, 'unit': 'g'},
            {'name': '大蒜', 'quantity': 2, 'unit': 'piece', 'notes': '切片'},
            {'name': '欧芹', 'quantity': 5, 'unit': 'g', 'notes': '切碎，可选'},
            {'name': '黑胡椒', 'quantity': 1, 'unit': 'tsp', 'notes': '现磨'},
            {'name': '食盐', 'quantity': 0.5, 'unit': 'tsp'},
            {'name': '橄榄油', 'quantity': 1, 'unit': 'tbsp'},
        ],
        'steps': [
            '三文鱼排用厨房纸吸干水分，两面均匀撒上盐和黑胡椒，腌制10分钟。',
            '平底锅烧热，倒入橄榄油，油热后将三文鱼皮朝下放入锅中。',
            '中火煎约3-4分钟，直到鱼皮变得金黄酥脆，期间可用锅铲轻轻按压，确保受热均匀。',
            '翻面，继续煎2-3分钟，或至你喜欢的熟度。将煎好的三文鱼盛出。',
            '转小火，在同一个锅中放入黄油，待其融化后加入蒜片，炒出香味。',
            '挤入半个柠檬的汁，快速搅拌均匀，形成柠檬黄油汁。',
            '关火，撒入切碎的欧芹（如果使用）。',
            '将做好的柠檬黄油汁淋在三文鱼上，旁边可配几片新鲜柠檬作装饰。'
        ]
    },
    {
        'recipe': {'title': '麻婆豆腐', 'description': '川菜经典，麻辣鲜香，口感滑嫩，非常下饭。', 'cooking_time_minutes': 20, 'difficulty': 2, 'cuisine_type': '川菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '豆腐', 'quantity': 1, 'unit': 'piece', 'notes': '用嫩豆腐或内酯豆腐'},
            {'name': '牛肉', 'quantity': 50, 'unit': 'g', 'notes': '切末，可用猪肉代替'},
            {'name': '豆瓣酱', 'quantity': 1.5, 'unit': 'tbsp'},
            {'name': '花椒', 'quantity': 1, 'unit': 'tsp', 'notes': '或花椒粉'},
            {'name': '干辣椒', 'quantity': 4, 'unit': 'piece', 'notes': '切段'},
            {'name': '大蒜', 'quantity': 3, 'unit': 'piece', 'notes': '切末'},
            {'name': '生姜', 'quantity': 1, 'unit': 'piece', 'notes': '小块，切末'},
            {'name': '葱', 'quantity': 1, 'unit': 'piece', 'notes': '切葱花'},
            {'name': '淀粉', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '酱油', 'quantity': 1, 'unit': 'tbsp'},
        ],
        'steps': ['豆腐切小块，入沸水焯烫一下捞出。', '锅中倒油，炒香牛肉末，加入豆瓣酱、干辣椒、姜蒜末炒出红油。', '加入适量水或高汤，放入豆腐，加入酱油，轻轻推动。', '煮沸后，分两到三次淋入水淀粉勾芡。', '出锅前撒上花椒粉和葱花即可。']
    },
    {
        'recipe': {'title': '宫保鸡丁', 'description': '糊辣荔枝味型，鸡肉滑嫩，花生香脆，酸甜微辣。', 'cooking_time_minutes': 25, 'difficulty': 2, 'cuisine_type': '川菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '鸡胸肉', 'quantity': 250, 'unit': 'g', 'notes': '切丁'},
            {'name': '花生', 'quantity': 50, 'unit': 'g', 'notes': '油炸或烤熟'},
            {'name': '干辣椒', 'quantity': 10, 'unit': 'g'},
            {'name': '花椒', 'quantity': 1, 'unit': 'tsp'},
            {'name': '大葱', 'quantity': 1, 'unit': 'piece', 'notes': '切段'},
            {'name': '生姜', 'quantity': 2, 'unit': 'slice'},
            {'name': '大蒜', 'quantity': 2, 'unit': 'piece'},
            {'name': '酱油', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '醋', 'quantity': 2, 'unit': 'tbsp'},
            {'name': '白砂糖', 'quantity': 1.5, 'unit': 'tbsp'},
            {'name': '料酒', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '淀粉', 'quantity': 2, 'unit': 'tbsp'},
        ],
        'steps': ['鸡丁用盐、料酒、蛋清、淀粉抓匀上浆。', '用酱油、醋、糖、料酒、水淀粉调成碗汁。', '热锅冷油，滑炒鸡丁至变色盛出。', '锅中留底油，小火炒香干辣椒和花椒，再放入葱姜蒜炒香。', '倒入鸡丁，烹入调好的碗汁，大火快速翻炒。', '最后加入炸花生米，翻炒均匀即可出锅。']
    },
    {
        'recipe': {'title': '鱼香肉丝', 'description': '不见鱼而有鱼味，咸甜酸辣兼备，肉丝滑嫩，是米饭杀手。', 'cooking_time_minutes': 25, 'difficulty': 2, 'cuisine_type': '川菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '里脊肉', 'quantity': 250, 'unit': 'g', 'notes': '切丝'},
            {'name': '木耳', 'quantity': 5, 'unit': 'g', 'notes': '泡发后切丝'},
            {'name': '胡萝卜', 'quantity': 0.5, 'unit': 'piece', 'notes': '切丝'},
            {'name': '青椒', 'quantity': 0.5, 'unit': 'piece', 'notes': '切丝'},
            {'name': '豆瓣酱', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '泡椒', 'quantity': 20, 'unit': 'g', 'notes': '切碎，可选'},
            {'name': '醋', 'quantity': 2, 'unit': 'tbsp'},
            {'name': '白砂糖', 'quantity': 1.5, 'unit': 'tbsp'},
            {'name': '酱油', 'quantity': 1, 'unit': 'tbsp'},
        ],
        'steps': ['肉丝加盐、料酒、淀粉抓匀上浆。', '木耳、胡萝卜、青椒切丝备用。', '调制鱼香汁：酱油、醋、糖、盐、水淀粉混合。', '热锅滑炒肉丝，变色后盛出。', '锅中留底油，炒香姜蒜末、豆瓣酱和泡椒。', '倒入配菜丝翻炒，再加入肉丝。', '淋入鱼香汁，大火快速翻炒均匀即可。']
    },
    {
        'recipe': {'title': '地三鲜', 'description': '东北名菜，土豆、茄子、青椒三种时令蔬菜的完美结合，咸香入味，极其下饭。', 'cooking_time_minutes': 30, 'difficulty': 2, 'cuisine_type': '东北菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '土豆', 'quantity': 1, 'unit': 'piece', 'notes': '切滚刀块'},
            {'name': '茄子', 'quantity': 1, 'unit': 'piece', 'notes': '切滚刀块'},
            {'name': '青椒', 'quantity': 1, 'unit': 'piece', 'notes': '切块'},
            {'name': '大蒜', 'quantity': 4, 'unit': 'piece', 'notes': '切末'},
            {'name': '酱油', 'quantity': 2, 'unit': 'tbsp'},
            {'name': '蚝油', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '白砂糖', 'quantity': 1, 'unit': 'tsp'},
            {'name': '淀粉', 'quantity': 1, 'unit': 'tbsp'},
        ],
        'steps': ['土豆、茄子、青椒分别过油炸至表面金黄捞出控油。', '调一碗芡汁：酱油、蚝油、糖、盐、淀粉和少量水混合。', '锅中留少许底油，爆香蒜末。', '倒入炸好的三样蔬菜，快速翻炒。', '淋入调好的芡汁，大火翻炒均匀，让汤汁包裹住所有食材即可。']
    },
    {
        'recipe': {'title': '猪肉炖粉条', 'description': '东北菜的代表之一，五花肉肥而不腻，粉条滑爽筋道，吸饱了肉汤的精华。', 'cooking_time_minutes': 70, 'difficulty': 2, 'cuisine_type': '东北菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '五花肉', 'quantity': 500, 'unit': 'g', 'notes': '切大块'},
            {'name': '粉条', 'quantity': 100, 'unit': 'g', 'notes': '提前用温水泡软'},
            {'name': '大白菜', 'quantity': 200, 'unit': 'g', 'notes': '可选，切片'},
            {'name': '八角', 'quantity': 2, 'unit': 'piece'},
            {'name': '花椒', 'quantity': 1, 'unit': 'tsp'},
            {'name': '香叶', 'quantity': 2, 'unit': 'piece'},
            {'name': '酱油', 'quantity': 3, 'unit': 'tbsp'},
            {'name': '冰糖', 'quantity': 15, 'unit': 'g'},
        ],
        'steps': ['五花肉焯水后捞出。', '锅中炒糖色，放入五花肉翻炒上色。', '加入葱姜、八角、花椒、香叶炒香。', '烹入料酒，加入酱油，倒入足量开水。', '大火烧开转小火炖40分钟。', '加入泡软的粉条和白菜，继续炖煮15-20分钟。', '最后加盐调味，大火收汁即可。']
    },
    {
        'recipe': {'title': '清蒸鲈鱼', 'description': '粤菜经典，做法简单，最大程度保留了鱼肉的鲜嫩原味。', 'cooking_time_minutes': 20, 'difficulty': 1, 'cuisine_type': '粤菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '鲈鱼', 'quantity': 1, 'unit': 'piece', 'notes': '约500g，处理干净'},
            {'name': '大葱', 'quantity': 1, 'unit': 'piece', 'notes': '部分切段，部分切丝'},
            {'name': '生姜', 'quantity': 1, 'unit': 'piece', 'notes': '部分切片，部分切丝'},
            {'name': '红椒', 'quantity': 0.5, 'unit': 'piece', 'notes': '切丝点缀'},
            {'name': '蒸鱼豉油', 'quantity': 3, 'unit': 'tbsp', 'notes': '或生抽'},
            {'name': '花生油', 'quantity': 2, 'unit': 'tbsp'},
        ],
        'steps': ['鲈鱼处理干净，两面划几刀，用葱段姜片和料酒腌制10分钟。', '盘底铺上葱段姜片，放上鲈鱼，鱼身上也放上葱姜。', '蒸锅水开后，放入鲈鱼，大火蒸8-10分钟。', '取出蒸好的鱼，倒掉盘中多余的汤汁，捡去葱姜。', '在鱼身上重新铺上新的葱丝、姜丝、红椒丝。', '淋上蒸鱼豉油。', '将花生油烧至冒烟，均匀地浇在葱姜丝上，激出香味即可。']
    },
    {
        'recipe': {'title': '白灼虾', 'description': '做法极简的粤式海鲜，突出虾的鲜甜本味，口感Q弹。', 'cooking_time_minutes': 10, 'difficulty': 1, 'cuisine_type': '粤菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '基围虾', 'quantity': 500, 'unit': 'g'},
            {'name': '生姜', 'quantity': 3, 'unit': 'slice'},
            {'name': '大葱', 'quantity': 1, 'unit': 'piece', 'notes': '切段'},
            {'name': '料酒', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '酱油', 'quantity': 2, 'unit': 'tbsp', 'notes': '蘸料用'},
            {'name': '芥末', 'quantity': 1, 'unit': 'tsp', 'notes': '蘸料用，可选'},
        ],
        'steps': ['虾剪去虾须，挑去虾线，洗净。', '锅中加水，放入姜片、葱段、料酒，大火烧开。', '水开后放入处理好的虾。', '煮至虾身变红卷曲，约2-3分钟即可捞出。', '立即放入冰水中浸泡，使虾肉更Q弹。', '用酱油和芥末调制蘸料，搭配食用。']
    },
    {
        'recipe': {'title': '意式肉酱面', 'description': '全球闻名的意大利美食，浓郁的番茄肉酱搭配劲道的意面，百吃不厌。', 'cooking_time_minutes': 45, 'difficulty': 2, 'cuisine_type': '西餐', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '意面', 'quantity': 200, 'unit': 'g'},
            {'name': '牛肉', 'quantity': 150, 'unit': 'g', 'notes': '切末'},
            {'name': '番茄', 'quantity': 2, 'unit': 'piece', 'notes': '去皮切丁'},
            {'name': '洋葱', 'quantity': 0.5, 'unit': 'piece', 'notes': '切末'},
            {'name': '胡萝卜', 'quantity': 0.5, 'unit': 'piece', 'notes': '切末'},
            {'name': '芹菜', 'quantity': 1, 'unit': 'piece', 'notes': '切末'},
            {'name': '番茄膏', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '红酒', 'quantity': 50, 'unit': 'ml', 'notes': '可选'},
            {'name': '罗勒', 'quantity': 5, 'unit': 'g', 'notes': '新鲜或干的'},
            {'name': '帕玛森奶酪', 'quantity': 20, 'unit': 'g', 'notes': '擦碎'},
        ],
        'steps': ['锅中加水和盐，煮意面至包装说明时间，捞出拌少许橄榄油备用。', '另起一锅，用橄榄油炒香洋葱、胡萝卜、芹菜末。', '加入牛肉末，炒至变色。', '加入番茄丁和番茄膏，翻炒均匀。', '烹入红酒，加入适量水或高汤，以及罗勒、盐、黑胡椒。', '小火慢炖30分钟，至酱汁浓稠。', '将肉酱淋在煮好的意面上，撒上帕玛森奶酪碎即可。']
    },
    {
        'recipe': {'title': '培根奶油意面 (Carbonara)', 'description': '正宗的意式奶油培根面，用蛋黄和奶酪制作浓郁酱汁，而非淡奶油。', 'cooking_time_minutes': 20, 'difficulty': 2, 'cuisine_type': '西餐', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '意面', 'quantity': 200, 'unit': 'g'},
            {'name': '培根', 'quantity': 100, 'unit': 'g', 'notes': '或意式烟肉，切丁'},
            {'name': '鸡蛋黄', 'quantity': 3, 'unit': 'piece'},
            {'name': '帕玛森奶酪', 'quantity': 50, 'unit': 'g', 'notes': '擦碎'},
            {'name': '大蒜', 'quantity': 1, 'unit': 'piece'},
            {'name': '黑胡椒', 'quantity': 1, 'unit': 'tsp'},
        ],
        'steps': ['煮意面，同时在一个大碗里混合蛋黄、大部分帕玛森奶酪和大量黑胡椒。', '另起一锅，小火煸炒培根至出油香脆，加入拍扁的大蒜增香后取出大蒜。', '意面煮好后，沥干水分（保留一小碗煮面水），立刻倒入培根锅中，离火。', '迅速将意面和培根倒入蛋黄奶酪碗中，快速搅拌。', '利用意面的余温使酱汁变得浓稠顺滑，如果太干可加入少量煮面水调节。', '装盘后，再撒上一些奶酪和黑胡椒。']
    },
    {
        'recipe': {'title': '冬阴功汤', 'description': '泰国国汤，酸辣开胃，香料风味浓郁，充满异国情调。', 'cooking_time_minutes': 30, 'difficulty': 3, 'cuisine_type': '东南亚菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '虾', 'quantity': 200, 'unit': 'g'},
            {'name': '蘑菇', 'quantity': 100, 'unit': 'g', 'notes': '草菇或平菇'},
            {'name': '香茅', 'quantity': 2, 'unit': 'piece', 'notes': '拍扁切段'},
            {'name': '南姜', 'quantity': 3, 'unit': 'slice'},
            {'name': '青柠叶', 'quantity': 5, 'unit': 'piece', 'notes': '撕开'},
            {'name': '小番茄', 'quantity': 6, 'unit': 'piece', 'notes': '对半切'},
            {'name': '鱼露', 'quantity': 2, 'unit': 'tbsp'},
            {'name': '柠檬', 'quantity': 1, 'unit': 'piece', 'notes': '榨汁'},
            {'name': '冬阴功酱', 'quantity': 2, 'unit': 'tbsp'},
            {'name': '椰浆', 'quantity': 100, 'unit': 'ml', 'notes': '可选，增加浓郁口感'},
        ],
        'steps': ['锅中加水，放入香茅、南姜、青柠叶煮沸出味。', '加入冬阴功酱，搅拌均匀。', '放入蘑菇和小番茄，煮5分钟。', '放入处理好的虾，煮至变色。', '加入鱼露和柠檬汁调味。', '如果喜欢，可以加入椰浆搅拌均匀，增添风味。', '出锅前可撒上香菜点缀。']
    },
    {
        'recipe': {'title': '韩式泡菜炒饭', 'description': '利用剩余的泡菜和米饭制作的快手美食，酸辣可口，简单又满足。', 'cooking_time_minutes': 15, 'difficulty': 1, 'cuisine_type': '韩国料理', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '米饭', 'quantity': 300, 'unit': 'g', 'notes': '隔夜冷饭为佳'},
            {'name': '泡菜', 'quantity': 150, 'unit': 'g', 'notes': '切碎'},
            {'name': '五花肉', 'quantity': 80, 'unit': 'g', 'notes': '或培根，切片'},
            {'name': '洋葱', 'quantity': 0.25, 'unit': 'piece', 'notes': '切丁'},
            {'name': '鸡蛋', 'quantity': 1, 'unit': 'piece', 'notes': '煎一个太阳蛋'},
            {'name': '韩式辣酱', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '芝麻油', 'quantity': 1, 'unit': 'tsp'},
            {'name': '海苔', 'quantity': 1, 'unit': 'piece', 'notes': '剪碎'},
        ],
        'steps': ['锅中少油，煸炒五花肉至出油焦香。', '加入洋葱丁和泡菜碎，翻炒出香味。', '加入韩式辣酱，翻炒均匀。', '倒入冷米饭，用锅铲压散，与所有材料翻炒均匀。', '淋入芝麻油，翻炒几下即可出锅。', '装盘后，在炒饭上放一个煎好的太阳蛋，撒上海苔碎和白芝麻。']
    },
    {
        'recipe': {'title': '日式肥牛饭 (牛丼)', 'description': '经典的日式快餐，肥牛片鲜嫩，洋葱丝香甜，配上特制酱汁，盖在米饭上，美味无比。', 'cooking_time_minutes': 15, 'difficulty': 1, 'cuisine_type': '日本料理', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '肥牛', 'quantity': 200, 'unit': 'g'},
            {'name': '洋葱', 'quantity': 1, 'unit': 'piece', 'notes': '切丝'},
            {'name': '米饭', 'quantity': 300, 'unit': 'g'},
            {'name': '酱油', 'quantity': 3, 'unit': 'tbsp'},
            {'name': '味醂', 'quantity': 3, 'unit': 'tbsp'},
            {'name': '清酒', 'quantity': 3, 'unit': 'tbsp', 'notes': '或料酒'},
            {'name': '白砂糖', 'quantity': 1, 'unit': 'tbsp'},
            {'name': '鸡蛋', 'quantity': 1, 'unit': 'piece', 'notes': '可选，做温泉蛋'},
        ],
        'steps': ['在锅中混合酱油、味醂、清酒、糖和100ml水，煮开。', '加入洋葱丝，中火煮至变软。', '放入肥牛片，用筷子拨散，煮至变色即可关火。', '将煮好的肥牛和洋葱连同汤汁一起浇在热米饭上。', '可以搭配一个温泉蛋、撒上葱花和红姜丝。']
    },
    {
        'recipe': {'title': '芒果糯米饭', 'description': '泰国标志性甜点，香甜的芒果搭配咸甜交织的椰浆糯米饭，风味独特。', 'cooking_time_minutes': 40, 'difficulty': 2, 'cuisine_type': '东南亚菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '糯米', 'quantity': 200, 'unit': 'g', 'notes': '提前浸泡至少4小时'},
            {'name': '芒果', 'quantity': 1, 'unit': 'piece', 'notes': '成熟的大芒果'},
            {'name': '椰浆', 'quantity': 200, 'unit': 'ml'},
            {'name': '白砂糖', 'quantity': 3, 'unit': 'tbsp'},
            {'name': '食盐', 'quantity': 0.5, 'unit': 'tsp'},
            {'name': '绿豆', 'quantity': 10, 'unit': 'g', 'notes': '去皮绿豆，炒脆，可选'},
        ],
        'steps': ['浸泡好的糯米沥干，上锅蒸20-25分钟至熟透。', '将150ml椰浆、糖和盐在小锅中加热，搅拌至糖盐融化，不要煮沸。', '将热的椰浆汁倒入蒸好的热糯米饭中，快速搅拌均匀，然后盖上盖子焖15分钟。', '芒果去皮切片。', '将剩余的50ml椰浆加少许盐和糖煮至微稠，作为淋面酱汁。', '将焖好的糯米饭装盘，旁边摆上芒果片，淋上椰浆淋面，撒上脆绿豆即可。']
    },
    {
        'recipe': {'title': '红烧排骨', 'description': '色泽红亮，咸中带甜，肉质软烂脱骨，是宴客和家常的硬菜。', 'cooking_time_minutes': 60, 'difficulty': 2, 'cuisine_type': '家常菜', 'status': 'published'},
        'author_username': 'admin',
        'ingredients': [
            {'name': '排骨', 'quantity': 500, 'unit': 'g', 'notes': '斩块'},
            {'name': '生姜', 'quantity': 4, 'unit': 'slice'},
            {'name': '大葱', 'quantity': 1, 'unit': 'piece', 'notes': '切段'},
            {'name': '八角', 'quantity': 2, 'unit': 'piece'},
            {'name': '冰糖', 'quantity': 25, 'unit': 'g'},
            {'name': '酱油', 'quantity': 3, 'unit': 'tbsp'},
            {'name': '料酒', 'quantity': 2, 'unit': 'tbsp'},
        ],
        'steps': ['排骨冷水下锅，加姜片、料酒焯水后捞出。', '锅中少油，放入冰糖小火炒出糖色。', '倒入排骨翻炒，使其均匀裹上糖色。', '加入葱姜、八角炒香。', '淋入酱油和料酒，翻炒均匀。', '加入足量开水没过排骨，大火烧开转小火炖45-60分钟。', '最后大火收汁，至汤汁浓稠即可。']
    },
]

class Command(BaseCommand):
    help = 'Seeds the database with initial recipe data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clears all existing recipe-related data before seeding.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding process...'))

        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing recipe data...'))
            Review.objects.all().delete()
            RecipeStep.objects.all().delete()
            RecipeIngredient.objects.all().delete()
            Recipe.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))

        ingredient_cache = {ing.name: ing for ing in Ingredient.objects.all()}
        user_cache = {}

        for recipe_data in RECIPES_DATA:
            recipe_info = recipe_data['recipe']
            author_username = recipe_data['author_username']
            
            if author_username in user_cache:
                author = user_cache[author_username]
            else:
                author, created = User.objects.get_or_create(
                    username=author_username,
                    defaults={'email': f'{author_username}@example.com', 'password': 'password123'}
                )
                if created:
                    self.stdout.write(self.style.NOTICE(f'Created user: {author_username}'))
                user_cache[author_username] = author

            try:
                recipe, created = Recipe.objects.update_or_create(
                    title=recipe_info['title'],
                    author=author, # Use author object for uniqueness
                    defaults=recipe_info
                )
                if created:
                    self.stdout.write(f"  - Creating recipe: '{recipe.title}'")
                else:
                    self.stdout.write(self.style.WARNING(f"  - Updating recipe: '{recipe.title}'"))
                    recipe.steps.all().delete()
                    recipe.recipeingredient_set.all().delete()

            except IntegrityError:
                self.stdout.write(self.style.ERROR(f"Could not create or update recipe '{recipe_info['title']}'. Skipping."))
                continue

            steps_to_create = [
                RecipeStep(recipe=recipe, step_number=i + 1, description=desc)
                for i, desc in enumerate(recipe_data['steps'])
            ]
            if steps_to_create:
                RecipeStep.objects.bulk_create(steps_to_create)

            ingredients_to_create = []
            for ing_data in recipe_data['ingredients']:
                ingredient_name = ing_data['name']
                ingredient_obj = ingredient_cache.get(ingredient_name)
                if ingredient_obj:
                    ingredients_to_create.append(
                        RecipeIngredient(
                            recipe=recipe, ingredient=ingredient_obj,
                            quantity=ing_data['quantity'], unit=ing_data['unit'],
                            notes=ing_data.get('notes', '')
                        )
                    )
                else:
                    self.stdout.write(self.style.WARNING(f"    - Ingredient '{ingredient_name}' not found in database. Skipping for recipe '{recipe.title}'."))
            
            if ingredients_to_create:
                RecipeIngredient.objects.bulk_create(ingredients_to_create)

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))