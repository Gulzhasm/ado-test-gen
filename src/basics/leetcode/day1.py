#python's array is a list
my_list = [1, 2, 3, 4, 5]
my_list = ["alice", "bob", "charlie"]

print(my_list[0])
print(my_list[-1])

#modify list
my_list[1] = "bob_updated"
print(my_list)

#common list methods
my_list.append("david")
my_list.remove("alice")
my_list.pop()  # removes last item
#my_list.pop(0)  # removes first item
print(my_list)
print(len(my_list))

#loop through list
for item in my_list:
    print(item)

#creation of list using range
numbers = list(range(1, 11))  # creates a list of numbers from
for i, num in enumerate(numbers):
    print(f"Index: {i}, Number: {num}")

#list comprehension
squared_numbers = [x**2 for x in numbers]
print(squared_numbers)
#nested lists
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

print(matrix[1][2])  # Accessing element '6'

for row in matrix:
    for item in row:
        print(item)

#create a dictionary
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}
print(person["name"])

person["age"] = 31  # modify value
person["profession"] = "Engineer"  # add new key-value pair
print(person)

if "age" in person:
    print("Age is present in the dictionary")

#loop through dictionary
for key, value in person.items():
    print(f"{key}: {value}")

#dicts are often used for counting
count = {}
nums = [3,2,3]
for x in nums:
    count[x] = count.get(x,0) + 1
    if count[x] > len(nums) // 2:
        print(x)

#map() function

nums = [1, 2, 3, 4, 5]
result = list(map(lambda x: x * x, nums))

print(result)  # Output: [1, 4, 9, 16, 25]

result = [x *x for x in nums]
print(result)  # Output: [1, 4, 9, 16, 25]

#filter() function
nums = [1, 2, 3, 4, 5, 6]
even_nums = list(filter(lambda x: x % 2 == 0, nums))
print(even_nums)  # Output: [2, 4, 6]

even_nums = [x for x in nums if x % 2 == 0]
print(even_nums)  # Output: [2, 4, 6]

#reduce() function
from ast import List
from functools import reduce
nums = [1, 2, 3, 4, 5]
product = reduce(lambda x, y: x * y, nums)
print(product)  # Output: 120

product = 1
for x in nums:
    product *= x
print(product)  # Output: 120

class Solution(object):
    def majorityElement(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        count = {}
        for x in nums:
            count[x] = count.get(x, 0) + 1
            if count[x] > len(nums) // 2:
                return x
            
class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        count = {}
        for x in nums:
            count[x] = count.get(x, 0) + 1
            if count[x] > len(nums) // 2:
                return x