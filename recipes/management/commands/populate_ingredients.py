import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Loads ingredient data from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The CSV file path containing ingredient data.')
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of ingredients to create/update in a single batch operation.'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing ingredients if a name conflict occurs (based on name being unique). Default is to skip new entries with conflicting names.',
        )
        parser.add_argument(
            '--ignore-conflicts-on-create',
            action='store_true',
            help='If not updating, ignore new entries with names that already exist in the DB (requires DB support for IGNORE or ON CONFLICT DO NOTHING).',
        )

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']
        batch_size = options['batch_size']
        update_existing = options['update_existing']
        ignore_conflicts_on_create = options['ignore_conflicts_on_create']

        if update_existing and ignore_conflicts_on_create:
            raise CommandError("错误: '--update-existing' 和 '--ignore-conflicts-on-create' 参数不能同时使用。")

        self.stdout.write(self.style.SUCCESS(f"开始从 {csv_file_path} 导入食材数据..."))

        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors_count = 0

        valid_categories = [choice[0] for choice in Ingredient.CATEGORY_CHOICES]

        # 在 update_existing 模式下，我们需要确保待创建列表中的 name 是唯一的
        # 在不更新模式下，我们预先检查数据库中的 name
        existing_names_in_db = set()
        if not update_existing and not ignore_conflicts_on_create:
             # 在不更新模式下，预先获取数据库中的所有名字用于跳过
            existing_names_in_db = set(Ingredient.objects.values_list('name', flat=True))

        ingredients_to_create_list = []
        ingredients_to_update_list = []
        # 用于在 update_existing 模式下跟踪 CSV 中即将创建的唯一名称
        names_pending_creation = set()

        try:
            with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    raise CommandError(f"错误: CSV文件 '{csv_file_path}' 为空或没有表头。")

                required_headers = ['name', 'category']
                for header in required_headers:
                    if header not in reader.fieldnames:
                        raise CommandError(
                            f"错误: CSV文件必须包含表头 '{header}'. "
                            f"当前表头: {', '.join(reader.fieldnames)}"
                        )

                for row_num, row in enumerate(reader, 1):
                    # --- 新增: 跳过注释行或空行 ---
                    name_raw = row.get('name') # 使用 get 不带默认值，以便检查 None
                    if name_raw is None: # 如果 name 字段完全缺失
                         self.stderr.write(self.style.WARNING(f"第 {row_num} 行: 缺少 'name' 字段，跳过此行。"))
                         skipped_count += 1
                         continue

                    name = name_raw.strip()
                    if not name or name.startswith('#'): # 跳过空行和注释行
                        # self.stdout.write(self.style.NOTICE(f"第 {row_num} 行: 跳过空行或注释行: {name_raw}"))
                        skipped_count += 1
                        continue
                    # --- 跳过注释行结束 ---


                    try:
                        category_raw = row.get('category')
                        # 对于 category, description, image_url，允许它们缺失或为空字符串
                        category = category_raw.strip() if category_raw is not None else None
                        description_raw = row.get('description')
                        description = description_raw.strip() if description_raw is not None else None
                        image_url_raw = row.get('image_url')
                        image_url = image_url_raw.strip() if image_url_raw is not None else None


                        if category and category not in valid_categories:
                            self.stderr.write(self.style.WARNING(
                                f"第 {row_num} 行 (食材: {name}): 无效的分类 '{category}'. "
                                f"有效分类为: {', '.join(valid_categories)}. 跳过此行."
                            ))
                            skipped_count += 1
                            continue

                        # 检查 category 是否允许为空，如果模型不允许但 CSV 里为空，则跳过
                        if not category and not Ingredient._meta.get_field('category').blank:
                             self.stderr.write(self.style.WARNING(f"第 {row_num} 行 (食材: {name}): 'category' 不能为空，跳过此行。"))
                             skipped_count += 1
                             continue


                        if update_existing:
                            try:
                                # 尝试获取数据库中已存在的食材
                                existing_ingredient = Ingredient.objects.get(name=name)
                                changed = False
                                # 检查字段是否有变化，如果CSV中的值不是 None 且与数据库不同
                                if category is not None and existing_ingredient.category != category:
                                    existing_ingredient.category = category
                                    changed = True
                                if description is not None and existing_ingredient.description != description:
                                    existing_ingredient.description = description
                                    changed = True
                                if image_url is not None and existing_ingredient.image_url != image_url:
                                    existing_ingredient.image_url = image_url
                                    changed = True

                                if changed:
                                    ingredients_to_update_list.append(existing_ingredient)
                                else:
                                    # self.stdout.write(self.style.NOTICE(f"食材 '{name}' 数据无变化，跳过。"))
                                    skipped_count += 1 # 没有变化
                            except Ingredient.DoesNotExist:
                                # 如果数据库中不存在，则添加到待创建列表
                                # --- 新增: 在添加到待创建列表前，检查是否已在列表中 ---
                                if name in names_pending_creation:
                                    self.stdout.write(self.style.WARNING(f"第 {row_num} 行 (食材: {name}): 在CSV中发现重复条目，已添加到待创建列表，跳过此重复行。"))
                                    skipped_count += 1
                                else:
                                    ingredients_to_create_list.append(Ingredient(
                                        name=name, category=category, description=description, image_url=image_url
                                    ))
                                    names_pending_creation.add(name) # 标记此 name 已在待创建列表中
                                # --- 新增结束 ---

                        else: # 不更新现有，只创建新的
                            if name in existing_names_in_db and not ignore_conflicts_on_create:
                                self.stdout.write(self.style.NOTICE(f"食材 '{name}' 已存在且未选择更新或忽略冲突，跳过。"))
                                skipped_count += 1
                                continue
                            # 如果 ignore_conflicts_on_create 为 True，则直接加入创建列表，让 bulk_create 处理冲突
                            # 如果 ignore_conflicts_on_create 为 False 且 name 不在 existing_names_in_db 中，也加入创建列表
                            # 在非 update_existing 模式下，理论上 CSV 中不应有重复名
                            ingredients_to_create_list.append(Ingredient(
                                name=name, category=category, description=description, image_url=image_url
                            ))


                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"处理第 {row_num} 行数据时出错 (食材: {name}): {e}"))
                        errors_count += 1
                        continue

                # 批量创建
                if ingredients_to_create_list:
                    self.stdout.write(f"准备批量创建 {len(ingredients_to_create_list)} 条新食材...")
                    # 使用 transaction.atomic() 保证批处理的原子性
                    try:
                        with transaction.atomic():
                            created_objects = Ingredient.objects.bulk_create(
                                ingredients_to_create_list,
                                batch_size=batch_size,
                                ignore_conflicts=ignore_conflicts_on_create
                            )
                            # 如果 ignore_conflicts=True, created_objects 将只包含实际创建的对象
                            # 否则，它将包含所有尝试创建的对象（如果没发生异常）
                            if ignore_conflicts_on_create:
                                # 实际创建数量需要通过其他方式计算，或者接受 bulk_create 的返回值
                                # 但 bulk_create(ignore_conflicts=True) 的返回值在不同DB backend行为可能不同
                                # 一个简单的方法是估算或再次查询计数，这里我们接受返回值的数量（如果有的话）
                                created_count_batch = len(created_objects) if created_objects is not None else 0
                                self.stdout.write(self.style.SUCCESS(f"尝试批量创建/忽略冲突 {len(ingredients_to_create_list)} 条食材完成，实际创建 (估算): {created_count_batch}"))
                                created_count += created_count_batch
                            else:
                                created_count_batch = len(created_objects) if created_objects is not None else 0
                                self.stdout.write(self.style.SUCCESS(f"成功批量创建 {created_count_batch} 条新食材。"))
                                created_count += created_count_batch

                    except IntegrityError as e:
                        # 在 update_existing 模式下，如果不忽略冲突且 CSV 有重复待创建项，会走到这里
                        self.stderr.write(self.style.ERROR(f"批量创建时发生 IntegrityError: {e}"))
                        self.stderr.write(self.style.NOTICE("请检查CSV中的name是否唯一，或使用 --ignore-conflicts-on-create (如果数据库支持)"))
                        errors_count += len(ingredients_to_create_list) # 假设整个批处理都算错误
                        # 注意：抛出异常后，update_existing 列表不会被处理

                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"批量创建时发生未知错误: {e}"))
                        errors_count += len(ingredients_to_create_list)
                        # 注意：抛出异常后，update_existing 列表不会被处理


                # 批量更新 (只有在批量创建没有发生未捕获异常时才会执行到这里)
                if ingredients_to_update_list:
                    self.stdout.write(f"准备批量更新 {len(ingredients_to_update_list)} 条食材...")
                    fields_to_update = ['category', 'description', 'image_url']
                    try:
                        with transaction.atomic():
                            updated_count_batch = Ingredient.objects.bulk_update(ingredients_to_update_list, fields_to_update, batch_size=batch_size)
                        updated_count += updated_count_batch
                        self.stdout.write(self.style.SUCCESS(f"成功批量更新 {updated_count_batch} 条食材。"))
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"批量更新时发生错误: {e}"))
                        errors_count += len(ingredients_to_update_list)

        except FileNotFoundError:
            raise CommandError(f'错误: 文件 "{csv_file_path}" 未找到.')
        except CommandError as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"处理文件时发生意外错误: {e}"))
            import traceback
            traceback.print_exc()
            return

        self.stdout.write(self.style.SUCCESS("--------------------"))
        self.stdout.write(self.style.SUCCESS("食材数据导入完成!"))
        self.stdout.write(f"总计尝试处理 CSV 行 (不含注释和空行): {row_num - skipped_count}")
        if not update_existing and not ignore_conflicts_on_create:
             self.stdout.write(f"总计数据库中已存在 (未更新): {skipped_count}")
        elif update_existing:
            self.stdout.write(f"总计数据无变化 (跳过更新): {skipped_count - errors_count}") # 减去错误行，因为错误行也可能被计入skipped
            self.stdout.write(f"总计更新: {updated_count}")

        self.stdout.write(f"总计创建: {created_count}")
        self.stdout.write(f"总计错误行: {errors_count}")
        self.stdout.write(f"总计因为CSV内部重复而跳过 (update模式): {len(ingredients_to_create_list) - created_count if update_existing and not ignore_conflicts_on_create else 0}")