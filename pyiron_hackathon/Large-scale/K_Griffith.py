from pyiron_workflow import as_function_node
from typing import Optional
import ase as _ase

@as_function_node("rotated_elast_tensor")
def rotate_elasticity_tensor(
    c11: Optional[float|int],
    c12: Optional[float|int],
    c13: Optional[float|int],
    c33: Optional[float|int],
    c44: Optional[float|int],
    crystal: Optional[str],
    x_indices: Optional[str|list[int]] = '1 0 0',
    y_indices: Optional[str|list[int]] = '0 1 0',
    z_indices: Optional[str|list[int]] = '0 0 1'
):
    '''
    Returns the elasticity tensor rotated in given orientation.
    Currently supports cubic, c14 and hcp structures.


        Parameters:
            c11, c12, c13, c33, c44: elastic constants in GPA
            crystal: hcp/c14/cubic(fcc, bcc etc.)
            x_indices, y_indices, z_indices: the desired miller indices for the three coordinate axes
    '''
    
    import numpy as np

    if isinstance(x_indices, str):
        x_indices = [int(i) for i in x_indices.split()]
    if isinstance(y_indices, str):
        y_indices = [int(i) for i in y_indices.split()]
    if isinstance(z_indices, str):
        z_indices = [int(i) for i in z_indices.split()]
    
    # base crystal orientation
    e1 = [1, 0, 0]; e2 = [0., 1., 0.]; e3 = [0, 0, 1]
    orient_dict = {'[0, 0, 0, 1]': [0, 0, 1], '[1, -1, 0, 0]': [0, 1, 0], '[-1, 1, 0, 0]': [0, -1, 0], '[1, 0, -1, 0]': [1, 0, 0], 
            '[-1, 0, 1, 0]': [-1, 0, 0],'[2, -1, -1, 0]': [1, 0, 0],'[-2, 1, 1, 0]': [-1, 0, 0], '[1, -2, 1, 0]': [0, -1, 0],
           '[-1, 2, -1, 0]': [0, 1, 0]}
    if crystal=='c14' or crystal=='hcp':
        m1 = orient_dict[str(x_indices)]
        m2 = orient_dict[str(y_indices)]
        m3 = orient_dict[str(z_indices)]
    else:
        m1 = x_indices
        m2 = y_indices
        m3 = z_indices 
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
def theor_K_griffith_plane_strain(
    C,
    gamma_s: Optional[float|int],
):
    '''
    Returns the theoretical Griffith fracture toughness for a desired material im MPa sqrt(m).


        Parameters:
            C: the elasticity tensor rotated to desired orientation
            gamma_s: Surface energy in J/m2
    '''

    import numpy as np

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

    L = 0.5 * np.real(1j*np.dot(AA,np.linalg.inv(BB)))
    lambda_coeff = np.linalg.inv(L)[1,1]
    K_GG = np.sqrt(2*gamma_s*lambda_coeff*10**9)*10**(-6)
    # print("Theoretical K Griffith is " + str(K_GG) + " MPa*m^1/2")
    
    return K_GG

@as_function_node("crack_param_dict")
def anisotropic_crack_params(
    C
):

    import numpy as np
    
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

    AB = np.concatenate((AA, BB), axis=0)
    J = np.zeros(np.shape(u))
    for i in range(3):
        J[i, i+3] = 1
        J[i+3, i] = 1
    AB_n = np.zeros(np.shape(u), dtype=complex)    
    for i in range(3):
        AB_n[:, i] = AB[:, i] / np.sqrt(np.matmul(AB[:, i].T, np.matmul(J, AB[:, i])))

    A = AB_n[0:3, 0:3]
    B = AB_n[3:6, 0:3]    
    B_inv = np.linalg.inv(B)

    return {'A': A, 'B_inv': B_inv, 'p': p}

@as_function_node("cracked_structure")
def displace_atoms_crack_aniso(
    atoms: _ase.Atoms, 
    K_I: Optional[int|float],
    K_II: Optional[int|float],
    K_III: Optional[int|float],
    crack_params: Optional[dict]
):

    import numpy as np
    import math

    A = crack_params['A']
    B_inv = crack_params['B_inv']
    p = crack_params['p']

    crack_struct = atoms.copy()
    
    pos_xyz = crack_struct.get_positions()
    X_c = crack_struct.cell[0][0]/2
    Y_c = crack_struct.cell[1][1]/2
    K_vector = [K_II, K_I, K_III]              # mode I and II are swapped below hence this order to keep the conventional modes
    
    for iii in range(len(pos_xyz)):
        x1 = pos_xyz[iii, 0] - X_c
        x2 = pos_xyz[iii, 1] - Y_c
        x3 = pos_xyz[iii, 2]    
        r = np.sqrt(x1**2 + x2**2)
        teta = math.atan2(x2, x1)
        p_diag = np.zeros((3, 3), dtype=complex)
        for i in range(3):
            p_diag[i, i] = np.sqrt(np.cos(teta) + p[i] * np.sin(teta))
        disp = np.sqrt(2 * r/np.pi) * np.real(A @ p_diag @ B_inv) @ K_vector
        crack_struct.positions[iii] += disp
    
    return crack_struct