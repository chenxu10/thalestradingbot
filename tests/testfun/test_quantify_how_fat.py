from scipy.optimize import fsolve

def equation(alpha):
    return (0.12/1.9)-(73.5/65)**(1-alpha)
    
x = fsolve(equation, 1)
print(x)