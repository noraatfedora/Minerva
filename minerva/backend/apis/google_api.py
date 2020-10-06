import requests
from os import environ
from json import  loads
from db import users, conn
from sqlalchemy import select, and_

def matrix(origins, destinations):
    # Example URL:
    #https://maps.googleapis.com/maps/api/distancematrix/json?origins=Boston,MA|Charlestown,MA&destinations=Lexington,MA|Concord,MA&departure_time=now&key=YOUR_API_KEY
    requestString = ("https://maps.googleapis.com/maps/api/distancematrix/json?origins="
        + addAdresses(origins)
        + "&destinations="
        + addAdresses(destinations)
        + "&departure_time=now"
        + "&key="
        + environ['GOOGLE_API']
    )

    return loads(requests.get(requestString).content)

def directions(origin, destination, waypoints):
    requestString = ("https://maps.googleapis.com/maps/api/directions/json?origin="
        + origin
        + "&destination="
        + destination
        + "&waypoints=optimize:true"
        + addAdresses(waypoints)
        + "&key="
        + environ['GOOGLE_API'])
    return loads(requests.get(requestString).content)

# Returns a sorted list of the order ID's
def getOrdering(origin, destination, orderList):
    # Uncomment for fast testing
    return [[2, 114, 264, 454, 327, 405, 137, 144, 474, 333, 229, 456, 321, 128, 216, 59, 178, 2], [2, 207, 19, 407, 147, 256, 159, 162, 208, 226, 233, 426, 65, 97, 244, 261, 205, 2], [2, 2], [2, 67, 54, 379, 290, 484, 53, 422, 113, 259, 357, 373, 72, 268, 439, 32, 491, 2], [2, 2], [2, 319, 110, 429, 461, 265, 496, 112, 196, 306, 184, 223, 73, 432, 352, 427, 2], [2, 170, 483, 466, 478, 402, 120, 366, 325, 14, 160, 41, 221, 359, 250, 451, 117, 2], [2, 2], [2, 2], [2, 413, 75, 328, 384, 86, 236, 382, 386, 311, 145, 436, 192, 279, 218, 371, 294, 2], [2, 2], [2, 476, 198, 18, 376, 37, 421, 377, 324, 182, 142, 455, 314, 135, 133, 181, 166, 2], [2, 392, 358, 83, 475, 187, 11, 431, 46, 287, 109, 237, 430, 16, 411, 497, 2], [2, 353, 156, 68, 81, 344, 343, 85, 445, 390, 313, 447, 401, 469, 355, 155, 275, 2], [2, 416, 43, 202, 100, 249, 316, 354, 485, 305, 462, 22, 394, 477, 89, 60, 138, 2], [2, 406, 200, 481, 317, 124, 271, 492, 235, 482, 273, 246, 212, 161, 152, 98, 301, 2], [2, 408, 149, 365, 220, 225, 136, 468, 228, 154, 26, 87, 312, 172, 381, 277, 410, 2], [2, 24, 336, 397, 42, 121, 267, 38, 52, 39, 307, 163, 254, 260, 171, 320, 393, 2], [2, 443, 219, 460, 280, 12, 148, 418, 95, 241, 472, 21, 435, 335, 168, 23, 104, 2], [2, 91, 186, 134, 173, 276, 295, 299, 349, 378, 310, 82, 115, 334, 340, 158, 193, 2], [2, 63, 346, 467, 369, 195, 243, 58, 404, 329, 197, 270, 464, 288, 2], [2, 213, 169, 175, 350, 361, 217, 179, 118, 27, 201, 274, 131, 177, 165, 126, 36, 2], [2, 92, 209, 248, 238, 490, 440, 428, 423, 420, 412, 370, 341, 283, 50, 130, 356, 2], [2, 106, 141, 266, 47, 206, 232, 143, 389, 459, 13, 380, 94, 293, 318, 326, 194, 2], [2, 227, 479, 330, 29, 364, 296, 342, 372, 69, 214, 257, 398, 102, 96, 286, 486, 2], [2, 2], [2, 493, 132, 444, 80, 111, 77, 425, 190, 323, 167, 203, 119, 176, 40, 400, 140, 2], [2, 239, 363, 230, 450, 442, 298, 247, 494, 231, 189, 446, 234, 285, 64, 488, 269, 2], [2, 183, 84, 463, 368, 292, 93, 116, 403, 304, 272, 51, 453, 174, 433, 419, 2], [2, 2], [2, 281, 284, 291, 108, 282, 78, 458, 331, 424, 332, 57, 415, 17, 452, 473, 258, 2], [2, 180, 123, 337, 263, 127, 204, 125, 99, 252, 79, 414, 278, 211, 30, 387, 367, 2], [2, 351, 224, 395, 480, 300, 48, 15, 157, 90, 103, 245, 347, 471, 215, 66, 251, 2], [2, 146, 441, 242, 345, 139, 45, 240, 437, 495, 385, 315, 338, 107, 457, 35, 188, 2], [2, 44, 49, 210, 191, 129, 465, 302, 489, 28, 374, 308, 222, 88, 2], [2, 62, 399, 417, 438, 61, 74, 164, 262, 255, 34, 388, 150, 375, 322, 348, 55, 2], [2, 105, 185, 56, 76, 309, 449, 122, 434, 487, 391, 448, 362, 71, 396, 383, 253, 2], [2, 101, 199, 409, 339, 151, 31, 303, 70, 153, 297, 25, 360, 470, 20, 33, 289, 2], [2, 2], [2, 2]]
    if orderList == []:
        return []
    addresses = []
    for order in orderList:
        user = conn.execute(users.select().where(users.c.id==order.userId)).fetchone()
        addresses.append(user.address)
    print("Origin: " + origin)
    print("Dest: " + destination)
    print("waypoints: " + str(addresses))
    response = directions(origin, destination, addresses)
    waypoint_order = response['routes'][0]['waypoint_order']
    toReturn = []
    for index in waypoint_order:
        toReturn.append(orderList[index].id)
    return toReturn

def addAdresses(addresses):
    toReturn = ''
    for address in addresses:
        # security
        address.replace('&', '')
        address.replace('|', '')
        
        toReturn += "|" + address
    return toReturn
