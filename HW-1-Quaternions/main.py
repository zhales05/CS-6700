def multiply(q1, q2):
    a1, b1, c1, d1 = q1
    a2, b2, c2, d2 = q2
    return [
        # i² = j² = k² = ijk = −1
        a1*a2 - b1*b2 - c1*c2 - d1*d2,  # real part
        a1*b2 + b1*a2 + c1*d2 - d1*c2,  # i part
        a1*c2 - b1*d2 + c1*a2 + d1*b2,  # j part
        a1*d2 + b1*c2 - c1*b2 + d1*a2   # k part
    ]
    
i = [0, 1, 0, 0] 
j = [0, 0, 1, 0]

ij = multiply(i, j)
ji = multiply(j, i)

print(f"i * j = {ij}")  
print(f"j * i = {ji}") 
print(f"Equal? {ij == ji}")  