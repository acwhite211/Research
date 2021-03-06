'''
regMVMT

var_name -> notation : dimension : use/discription
or
var_name -> use/discription

Define:
T -> # of Tasks
V -> # of Views
t -> task index
v -> view index
N -> # of labeled samples
M -> # of unlabeled samples
D -> # of features

Input:
y -> y_t : [T] : y[t] -> [N_t x 1] label column vector
X -> X_t : [T] : X[t] -> [N_v x D_v] labeled feature matrix
U -> U_t : [T] : U[t] -> [M_v x D_v] unlabeled feature matrix
lambda ->  regularization parameter
mu -> regularization parameter
iterations -> N_it
epsilson -> regularization parameter

Algorithm:
W0 -> W_0 :
Omega0 -> Omega_v0 : [V] : Omega0[v] -> 
I -> I_d : [T x V] : I[t, v] -> 1 for labeled samples and 0 for unlabeled samples
A -> A_tv -> [T x V] : A[t, v] -> [D_v x D_v] matrix
B -> B_vv'_t -> [T x V] : B[t, v, v'] -> [D_v x D_v] matrix
C -> C_tv : [T x V] : C[t', v] = [D_v x D_v] matrix
E -> E_t_v : [T x V] : E[t, v] -> [D_v x 1] column matrix
L -> L : [TD x TD] : L[i, j] -> value
R -> R : [TD x 1] column matrix
W -> W : [TD x 1] column matrix
w -> w_t_v : [T x V] : w[t, v] -> [D_v x 1] column vector of weights
W_v -> W-v : [V] : W_v[v] -> [D_v x T] matrix where column t is w_t_v

Output:
W_t -> W_t : [D x T] : weights matrix
Omega -> Omega_v : [V] : Omega[v] -> [T x T] similarity matrix

'''

import numpy as np

class Reg_MVMT(object):
    def __init__(self, task_views, task_labels, views):
        self.task_views = task_views # {task_key : view_keys}
        self.task_labels = task_labels # {task_key : sample_values}
        self.views = views # {view_key : feature_matrix}
        
    def train(self, iterations=100, lambda_var=.01, mu=0.01, gamma=.01, epsilon=.01):
        T = len(self.task_labels.keys())
        V = len(self.views.keys())
        D = sum([x.shape[1] for x in self.views.values()])
        y = {}
        X = {}
        U = {}
        I = np.matrix(np.ones((T, V)))
        L = np.matrix((T * V, T * V))
        w_t_v = {}
        W = np.matrix(np.zeros((T * D, 1)))
        W_t = np.matrix(np.zeros((D, T)))
        W_v = {}
        Omega = {}

        # build I
        for t in self.task_labels.keys():
            for v in self.views.keys():
                if v in self.task_views[t]:
                    I[t, v] = 1
                else:
                    I[t, v] = 0
                
        # build y, X, and U
        for t in range(T):
            for v in range(V):
                m = self.views[v].tolist()
                x = []
                u = []
                y_t = []
                for s in range(len(m)):
                    if self.task_labels[t][s] != 0.0:
                        x.append(m[s])
                        y_t.append(self.task_labels[t][s])
                    else:
                        u.append(m[s])
                X[t, v] = np.matrix(x)
                y[t] = np.matrix(y_t).T
                U[t, v] = np.matrix(u)
                w[t, v] = np.martix(np.ones(X[t, v].shape[1], 1))
                    
        # initialize W0
        W0 = np.matrix(np.zeros((T * D, 1)))

        # initialize Omega0
        Omega0 = {}
        for v in range(V):
            I_T = np.matrix(np.identity(T))
            Omega0[v] = (1 / T) * I_T
            Omega[v] = Omega0[v]

        for iteration in range(iterations):
            A = {}
            B = {}
            C = {}
            E = {}

            for t in self.task_labels.keys():
                for v in self.views.keys():
                    # construct A[t, v]
                    A[t, v] = lambda_var + (mu * (V - 1) * U[t, v].T * U[t, v]) + \
                              ((X[t, v].T * X[t, v]) / (V ** 2))
    
                    # construct E[t, v]
                    E[t, v] = (X[t, v].T * y[t]) / V
    
                    # construct B[t, v, v']
                    for v2 in range(V):
                        if v != v2:
                            B[t, v, v2] = ((X[t, v].T * X[t, v2]) / (V ** 2)) - \
                                          (mu * U[t, v].T * U[t, v2])
    
                    # construct C[t', v]
                    for t2 in range(T):
                        if t != t2:
                            I_Dv = np.matrix(np.identity(self.views[v].shape[1]))
                            C[t2, v] = gamma * Omega[v][t, t2] * I_Dv

            # construct L
            L = np.zeros((T * D, T * D))
            i_offset = 0
            j_offset = 0
            for t in range(T):
                row_index = 0
                for v in range(V):
                    for t2 in range(T):
                        if t == t2:
                            for v2 in range(V):
                                if v == v2:
                                    for i in range(A[t, v].shape[0]):
                                        for j in range(A[t, v].shape[1]):
                                            L[i + i_offset, j + j_offset] = A[t, v][i, j]
                                    j_offset += A[t, v].shape[1]
                                else:
                                    for i in range(B[t, v, v2].shape[0]):
                                        for j in range(B[t, v, v2].shape[1]):
                                            L[i + i_offset, j + j_offset] = B[t, v, v2][i, j]
                                    j_offset += B[t, v, v2].shape[1]
                        else:
                            for v2 in range(V):
                                if v == v2:
                                    for i in range(C[t, v].shape[0]):
                                        for j in range(C[t, v].shape[1]):
                                            L[i + i_offset, j + j_offset] = C[t, v][i, j]
                                    j_offset += C[t, v].shape[1]
                                else:
                                    j_offset += C[t, v2].shape[1]
                    i_offset += A[t, row_index].shape[0]
                    j_offset = 0
                    row_index += 1
            L = np.matrix(L)

            # construct R -> column vector
            R = []
            for t in range(T):
                for v in range(V):
                    R.extend(E[(t, v)].T.tolist()[0])
            R = np.matrix(R).T

            # compute W
            W = L.I * R

            # construct W_v
            W_v = []
            for v in range(V):
                for t in range(T):
                    W_v.append(w[t, v].T.tolist()[0])
            W_v = np.matrix(W_v).T

            # update Omega[v]
            for v in range(V):
                Omega[v] = ((W_v.T * W_v) ** (1 / 2)) / (sum(np.diag((W_v.T * W_v) ** (1 / 2)).tolist()))

            is_finished = False
            if (np.linalg.norm(W - W0, 1) < epsilon):
                is_finished = True
                for v in range(V):
                    if (np.linalg.norm(W - W0, 1) >= epsilon):
                        is_finished = False
                        break
            if is_finished:
                break
            else:
                W0 = W
                for v in range(V):
                    Omega0[v] = Omega[v]

            # reconstruct W_t
            W_t = W_t.T.tolist()
            W_temp = W.T.tolist()[0]
            for t in range(T):
                W_t[t] = W_temp[t * D : (t * D) + D]
            W_t = np.matrix(W_t).T

        return (W_t, Omega)

