import numpy as np
from gym import Env, spaces, utils
from AM_Gyms.AM_Env_wrapper import AM_ENV
from AM_Gyms.ModelLearner import ModelLearner
from AM_Gyms.ModelLearner_Robust import ModelLearner_Robust
# from AM_Env_wrapper import AM_ENV
# from ModelLearner import ModelLearner
# from ModelLearner_Robust import ModelLearner_Robust
import os
import json

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class AM_Environment_tables():
    
    P:np.ndarray
    R:np.ndarray
    Q:np.ndarray
    
    StateSize:int
    ActionSize:int
    MeasureCost:int
    s_init:int
    
    def learn_model(self, env:Env):
        print("to be implemented!")
        
    def learn_model_AMEnv(self, env:AM_ENV, N = None):
        
        self.StateSize, self.ActionSize, self.MeasureCost, self.s_init = env.get_vars()
        
        if N == None:
            N = self.StateSize * self.ActionSize * 50   # just guessing how many are required...
        
        learner             = ModelLearner(env)
        learner.sample(N)
        self.P, self.R, _   = learner.get_model(transformed=True)
        self.Q              = learner.get_Q(transformed=True)
        
    def env_to_dict(self):
        return {
                    "P":            self.P,
                    "R":            self.Q,
                    "R":            self.R,
                    "StateSize":    self.StateSize,
                    "ActionSize":   self.ActionSize,
                    "MeasureCost":  self.MeasureCost,
                    "s_init":       self.s_init
                }
        
    def env_from_dict(self, dict):
        self.P, self.R, self.Q = dict["P"], dict["R"], dict["Q"]
        self.StateSize, self.ActionSize = dict["StateSize"], dict["ActionSize"]
        self.MeasureCost, self.s_init = dict["MeasureCost"], dict["s_init"]
        
    def export_model(self, fileName, folder = None):
        
        if folder is None:
            folder = os.getcwd()
            
        fullPath = os.path.join(folder,fileName)

        with open(fullPath, 'w') as outfile:
            json.dump(self.env_to_dict(), outfile, cls=NumpyEncoder)
    
    def import_model(self, fileName, folder=None):
        
        if folder is None:
            folder = os.getcwd()
            
        fullPath = os.path.join(folder,fileName)
        
        with open(fullPath, 'r') as outfile:
            model = json.load(outfile)
        
        self.env_from_dict(model)

class RAM_Environment_tables(AM_Environment_tables):
    
    Pmin:np.ndarray
    Pmax:np.ndarray
    
    PrMdp:np.ndarray
    QrMdp:np.ndarray
    
    def learn_model_AMEnv_alpha(self, env: Env, alpha:float, N=None, N_robust=None):
        
        self.StateSize, self.ActionSize, self.MeasureCost, self.s_init = env.get_vars()
        
        if N_robust is None:
            N_robust = self.StateSize*self.ActionSize * 10
        if N is None:
            N = self.StateSize * self.ActionSize * 100
            
        robustLearner = ModelLearner_Robust(env, alpha)
        robustLearner.run(updates=N_robust, eps_modelLearner=N)
        
        self.P, self.R, self.Q, self.QrMdp, self.PrMdp = robustLearner.get_model()
        self.Pmin, self.Pmax = np.maximum(self.P-alpha, 0), np.minimum(self.P+alpha, 1)

        
    def env_to_dict(self):
        dict_standard = super().env_to_dict()
        dict_robust =   {
                            "Pmin":    self.Pmin,
                            "Pmax":    self.Pmax,
                            "PrMdp":   self.PrMdp,
                            "QrMdp":   self.QrMdp
                        }
        return dict_standard | dict_robust
    
    def env_from_dict(self, dict):
        super().env_from_dict(dict)
        
        self.Pmin, self.Pmax    = dict["Pmin"] , dict["Pmax"]
        self.PrMdp, self.QrMdp  = dict["PrMdp"], dict["QrMdp"]



# Code for learning models:

directoryPath = os.path.join(os.getcwd(), "AM_Gyms", "Learned_Models")
alpha = 0.3

from AM_Gyms.MachineMaintenance import Machine_Maintenance_Env
from AM_Gyms.Loss_Env import Measure_Loss_Env
# from MachineMaintenance import Machine_Maintenance_Env

env_names           = ["Machine_Maintenance_a03", "Loss_a03"]

envs                = [Machine_Maintenance_Env(N=8), Measure_Loss_Env()]
env_stateSize       = [11,4]
env_actionSize      = [2,2]
env_sInit           = [0,0]

for (i,env) in enumerate(envs):
    AM_env = AM_ENV(env, env_stateSize[i], env_actionSize[i], 0, env_sInit[i])
    modelLearner = RAM_Environment_tables()
    modelLearner.learn_model_AMEnv_alpha(AM_env, alpha)
    modelLearner.export_model(env_names[i], directoryPath)