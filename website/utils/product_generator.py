from itertools import product
from website.models import Product, Category, Brand


def create_product_combinations():
    characteristics = {
        'петл': {
            'mounting_type': ['Накладная', 'Полунакладная', 'Вкладная', 'Фальш-планка'],
            'response_type': ['Прямая', 'Крестообразная'],
            'hinge_angle': ['83', '95', '110', '165'],
            'hinge_closing_type': ['с доводчиком', 'без доводчика', 'без пружинки']
        },
        'направля': {
            'mounting_type': ['Шариковые', 'Роликовые', 'Метабокс', 'Cкрытого_монтажа', 'Частички'],
            'runner_size': ['250', '270', '300', '310', '350', '360', '400', '410',
                            '450', '460', '500', '510', '550', '560', '600', '650', '700', '750']
        }
    }

    created_count = 0

    for category in Category.objects.all():
        category_name = category.name.lower()

        if 'петл' in category_name:
            char_dict = characteristics['петл']
            for brand in Brand.objects.all():
                for mount_type, resp_type, angle, closing_type in product(
                        char_dict['mounting_type'],
                        char_dict['response_type'],
                        char_dict['hinge_angle'],
                        char_dict['hinge_closing_type']
                ):
                    # Проверяем не существует ли уже
                    if not Product.objects.filter(
                            category=category,
                            brand=brand,
                            mounting_type=mount_type,
                            response_type=resp_type,
                            hinge_angle=angle,
                            hinge_closing_type=closing_type
                    ).exists():
                        product_name = f"{brand.name} {mount_type} {angle}° {resp_type}"
                        Product.objects.create(
                            name=product_name,
                            category=category,
                            brand=brand,
                            mounting_type=mount_type,
                            response_type=resp_type,
                            hinge_angle=angle,
                            hinge_closing_type=closing_type,
                            our_price=0
                        )
                        created_count += 1

        elif 'направля' in category_name:
            char_dict = characteristics['направля']
            for brand in Brand.objects.all():
                for mount_type, size in product(
                        char_dict['mounting_type'],
                        char_dict['runner_size']
                ):
                    if not Product.objects.filter(
                            category=category,
                            brand=brand,
                            mounting_type=mount_type,
                            runner_size=size
                    ).exists():
                        product_name = f"{brand.name} {mount_type} {size}мм"
                        Product.objects.create(
                            name=product_name,
                            category=category,
                            brand=brand,
                            mounting_type=mount_type,
                            runner_size=size,
                            our_price=0
                        )
                        created_count += 1

    return created_count