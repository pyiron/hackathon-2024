from pyiron_workflow import as_function_node
from typing import Optional

@as_function_node("rotated_elast_tensor")
def rotate_elasticity_tensor(
    c11: Optional[float|int],
    c12: Optional[float|int],
    c13: Optional[float|int],
    c33: Optional[float|int],
    c44: Optional[float|int],
    orient_x: Optional[list[int]],
    orient_y: Optional[list[int]],
    orient_z: Optional[list[int]],
    crystal: Optional[str]
):

    import numpy as np
    
    # base crystal orientation
    e1 = [1, 0, 0]; e2 = [0., 1., 0.]; e3 = [0, 0, 1]
    orient_dict = {'[0, 0, 0, 1]': [0, 0, 1], '[1, -1, 0, 0]': [0, 1, 0], '[-1, 1, 0, 0]': [0, -1, 0], '[1, 0, -1, 0]': [1, 0, 0], 
            '[-1, 0, 1, 0]': [-1, 0, 0],'[2, -1, -1, 0]': [1, 0, 0],'[-2, 1, 1, 0]': [-1, 0, 0], '[1, -2, 1, 0]': [0, -1, 0],
           '[-1, 2, -1, 0]': [0, 1, 0]}
    if crystal=='c14' or crystal=='hcp':
        m1 = orient_dict[str(orient_x)]
        m2 = orient_dict[str(orient_y)]
        m3 = orient_dict[str(orient_z)]
    else:
        m1 = orient_x
        m2 = orient_y
        m3 = orient_z 
    m1 /= np.linalg.norm(m1); m2 /= np.linalg.norm(m2); m3 /= np.linalg.norm(m3)
    Q = np.array([[np.matmul(m1,e1), np.matmul(m1,e2), np.matmul(m1,e3)], 
                  [np.matmul(m2,e1), np.matmul(m2,e2), np.matmul(m2,e3)], [np.matmul(m3,e1), np.matmul(m3,e2), np.matmul(m3,e3)]])
    K1 = np.array([[Q[0,0]**2, Q[0,1]**2, Q[0,2]**2], [Q[1,0]**2, Q[1,1]**2, Q[1,2]**2], [Q[2,0]**2, Q[2,1]**2, Q[2,2]**2]])
    K2 = np.array([[Q[0,1]*Q[0,2], Q[0,2]*Q[0,0], Q[0,0]*Q[0,1]], [Q[1,1]*Q[1,2], Q[1,2]*Q[1,0], Q[1,0]*Q[1,1]], [Q[2,1]*Q[2,2], Q[2,2]*Q[2,0], Q[2,0]*Q[2,1]]])
    K3 = np.array([[Q[1,0]*Q[2,0], Q[1,1]*Q[2,1], Q[1,2]*Q[2,2]], [Q[2,0]*Q[0,0], Q[2,1]*Q[0,1], Q[2,2]*Q[0,2]], [Q[0,0]*Q[1,0], Q[0,1]*Q[1,1], Q[0,2]*Q[1,2]]])
    K4 = np.array([[Q[1,1]*Q[2,2]+Q[1,2]*Q[2,1], Q[1,2]*Q[2,0]+Q[1,0]*Q[2,2], Q[1,0]*Q[2,1]+Q[1,1]*Q[2,0]], 
                   [Q[2,1]*Q[0,2]+Q[2,2]*Q[0,1], Q[2,2]*Q[0,0]+Q[2,0]*Q[0,2], Q[2,0]*Q[0,1]+Q[2,1]*Q[0,0]], 
                   [Q[0,1]*Q[1,2]+Q[0,2]*Q[1,1], Q[0,2]*Q[1,0]+Q[0,0]*Q[1,2], Q[0,0]*Q[1,1]+Q[0,1]*Q[1,0]]])
    KK1 = np.concatenate((K1, 2*K2), axis=1)
    KK2 = np.concatenate((K3, K4), axis=1)
    KK = np.concatenate((KK1, KK2), axis=0)

    # Material stiffness tensor
    if crystal=='c14' or crystal=='hcp':
        C_base = np.array([[c11, c12, c13, 0, 0, 0], [c12, c11, c13, 0, 0, 0], [c13, c13, c33, 0, 0, 0], 
                           [0, 0, 0, c44, 0, 0], [0, 0, 0, 0, c44, 0], [0, 0, 0, 0, 0, (c11-c12)/2]]) 
    else:
        C_base = np.array([[c11, c12, c12, 0, 0, 0], [c12, c11, c12, 0, 0, 0], [c12, c12, c11, 0, 0, 0], 
                           [0, 0, 0, c44, 0, 0], [0, 0, 0, 0, c44, 0], [0, 0, 0, 0, 0, c44]]) 
    C = np.dot(np.dot(KK, C_base), np.transpose(KK)) # Rotation of the material stiffness tensor

    return C

@as_function_node("theoretical_k_griffith")
def theoretical_griffith_fracture_toughness(
    C,
    gamma_s: Optional[float|int],
):

    import numpy as np
    A1 = np.linalg.inv(C) #Compliance tensor
    b11 = (A1[0,0]*A1[2,2]-A1[0,2]**2)/A1[2,2]
    b22 = (A1[1,1]*A1[2,2]-A1[1,2]**2)/A1[2,2]
    b12 = (A1[0,1]*A1[2,2]-A1[0,2]*A1[1,2])/A1[2,2]
    b66 = (A1[5,5]*A1[2,2]-A1[1,5]**2)/A1[2,2]
    Estar = ((b11*b22/2)*(np.sqrt(b22/b11)+(2*b12+b66)/(2*b11)))**(-0.5)

    QQ = np.array([[C[0,0], C[0,5], C[0,4]], [C[0,5], C[5,5], C[4,5]], [C[0,4], C[4,5], C[4,4]]])
    R = np.array([[C[0,5], C[0,1], C[0,3]], [C[5,5], C[1,5], C[3,5]], [C[4,5], C[1,4], C[3,4]]])
    T = np.array([[C[5,5], C[1,5], C[3,5]], [C[1,5], C[1,1], C[1,3]], [C[3,5], C[1,3], C[3,3]]])
    N1 = -1 * np.dot(np.linalg.inv(T),np.transpose(R))
    N2 = np.linalg.inv(T)
    N3 = np.dot(np.dot(R, np.linalg.inv(T)), np.transpose(R)) - QQ
    NN1 = np.concatenate((N1, N2), axis=1)
    NN2 = np.concatenate((N3, np.transpose(N1)), axis=1)
    N = np.concatenate((NN1, NN2), axis=0)

    #--- finding eigenvector and eigen values, ...
    [v, u] = np.linalg.eig(N) # v - eigenvalues, v - eigenvectors
    a1 = [[u[0,0]], [u[1,0]], [u[2,0]]]
    pp1 = v[0]
    b1 = np.dot(np.transpose(R)+np.dot(pp1, T),a1)

    a2 = [[u[0,2]], [u[1,2]], [u[2,2]]]
    pp2 = v[2]
    b2 = np.dot(np.transpose(R)+np.dot(pp2, T),a2)

    a3 = [[u[0,4]], [u[1,4]], [u[2,4]]]
    pp3 = v[4]
    b3 = np.dot(np.transpose(R)+np.dot(pp3, T),a3)
    AA = np.concatenate((a1, a2, a3), axis=1)
    BB = np.concatenate((b1, b2, b3), axis=1)

    p = np.array([pp1, pp2, pp3])

    L = 0.5 * np.real(1j*np.dot(AA,np.linalg.inv(BB)))
    lambda_coeff = np.linalg.inv(L)[1,1]
    K_GG = np.sqrt(2*gamma_s*lambda_coeff*10**9)*10**(-6)
    # print("Theoretical K Griffith is " + str(K_GG) + " MPa*m^1/2")
    
    return K_GG 