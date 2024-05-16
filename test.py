import datetime

# lst = [[31, 'jost2', 3, datetime.datetime(2024, 4, 19, 15, 30), datetime.datetime(2024, 4, 19, 18, 30), 
#         [['Goveji burger', 8], ['Ribeye steak', 22], ['T-bone steak', 25]]], 
#         [27, 'jost2', 5, datetime.datetime(2024, 4, 19, 18, 0), datetime.datetime(2024, 4, 19, 22, 0),
#         [['Pancetta solata', 7], ['Ribeye steak', 22], ['Tiramisu', 5]]]]

# lst = [item.strftime("%d. %m. %Y ob %H:%M") if isinstance(item, datetime.datetime) else item for item in lst]



# for sublist in lst:
#     for i in range(len(sublist)):
#         if isinstance(sublist[i], datetime.datetime):
#             sublist[i] = sublist[i].strftime("%d. %m. %Y ob %H:%M")


# lst = [
#     [53, 'jost2', 2, '26. 06. 2024 ob 19:35 uri', '26. 06. 2024 ob 21:35 uri', 
#      [['Crème Brûlée', 11, 1], ['T-bone steak', 50, 2]]
#     ]
# ]
# food_items = [name for entry in lst for name, price, quantity in entry[5] for _ in range(quantity)]
# print(", ".join(food_items))

lst = [1,2]

print()