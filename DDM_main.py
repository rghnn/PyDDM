'''
Simulation code for Drift Diffusion Model
Author: Norman Lam (norman.lam@yale.edu)
'''
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import matplotlib.cm as matplotlib_cm
import copy

########################################################################################################################
### Initialization
## Flags to run various parts or not
Flag_random_traces = 1 # Plot some traces that have somewhat arbitrary trajectories
Flag_Compare_num_analy_sim = 1 # Compare numerical solution to analytical solutions and/or simulations.
#Flag_coherence_tasks  = 1  # Do various tasks (fixed time, Psychophysical Kernel, Duration Paradigm, Pulse Paradigm). Nah... not a good idea to do this here...
Flag_Pulse = 0
Flag_Duration = 0
Flag_PK = 0

#Load parameters and functions
from DDM_parameters import *
from DDM_functions import *


########################################################################################################################
## Vary coherence and do each tasks (fixed-time, psychophysical kernel, Duration Paradigm, Pulse Paradigm)
models_list = [0,1,2,3,4]                                #List of models to use. See Setting_list
#models_list = models_list_all                                #List of models to use. See Setting_list

Prob_final_corr  = np.zeros((len(mu_0_list), len(models_list))) # total correct probability for each mu & model.
Prob_final_err   = np.zeros((len(mu_0_list), len(models_list))) # total erred probability for each mu & model.
Prob_final_undec = np.zeros((len(mu_0_list), len(models_list))) # total undecided probability for each mu & model.
Mean_Dec_Time    = np.zeros((len(mu_0_list), len(models_list)))

Prob_final_corr_Analy  = np.zeros((len(mu_0_list), 2))
Prob_final_err_Analy   = np.zeros((len(mu_0_list), 2))
Prob_final_undec_Analy = np.zeros((len(mu_0_list), 2))
Mean_Dec_Time_Analy    = np.zeros((len(mu_0_list), 2))


## Define an array to hold the data of simulations over all models, using the original parameters (mu_0)
Prob_final_corr_0  = np.zeros((len(models_list)))
Prob_final_err_0   = np.zeros((len(models_list)))
Prob_final_undec_0 = np.zeros((len(models_list)))
Mean_Dec_Time_0    = np.zeros((len(models_list)))

traj_mean_pos_all = np.zeros((len(t_list), len(models_list)))

### Compute the probability distribution functions for the correct and erred choices
# NOTE: First set T_dur to be the the duration of the fixed duration task.
for i_models in range(len(models_list)):
    index_model_2use = models_list[i_models]
    for i_mu0 in range(len(mu_0_list)):
        mu_temp = mu_0_list[i_mu0]
        (Prob_list_corr_temp, Prob_list_err_temp) = DDM_pdf_general([mu_temp, param_mu_x_list[index_model_2use], param_mu_t_list[index_model_2use], sigma_0, param_sigma_x_list[index_model_2use], param_sigma_t_list[index_model_2use], B, param_B_t_list[index_model_2use]], index_model_2use, 0)                               # Simple DDM
        Prob_list_sum_corr_temp  = np.sum(Prob_list_corr_temp)
        Prob_list_sum_err_temp  = np.sum(Prob_list_err_temp)
        Prob_list_sum_undec_temp  = 1 - Prob_list_sum_corr_temp - Prob_list_sum_err_temp


        #Outputs...
        # Forced Choices: The monkey will always make a decision: Split the undecided probability half-half for corr/err choices.
        Prob_final_undec[i_mu0, i_models] = Prob_list_sum_undec_temp
        Prob_final_corr[i_mu0, i_models]  = Prob_list_sum_corr_temp + Prob_final_undec[i_mu0, i_models]/2.
        Prob_final_err[i_mu0, i_models]   = Prob_list_sum_err_temp  + Prob_final_undec[i_mu0, i_models]/2.
        # Mean_Dec_Time[i_mu0, i_models]    = np.sum((Prob_list_corr_temp+Prob_list_err_temp) *t_list) / np.sum((Prob_list_corr_temp+Prob_list_err_temp))   # Regardless of choice made. Note that Mean_Dec_Time does not includes choices supposedly undecided and made at the last moment.
        Mean_Dec_Time[i_mu0, i_models]    = np.sum((Prob_list_corr_temp)*t_list) / np.sum((Prob_list_corr_temp))   # Regardless of choice made. Note that Mean_Dec_Time does not includes choices supposedly undecided and made at the last moment.

        ##Normalize to fit to the analytical solution. (Anderson 1960)
        if index_model_2use ==1 or index_model_2use ==2:
            Prob_final_corr[i_mu0, i_models] = Prob_list_sum_corr_temp / (Prob_list_sum_corr_temp + Prob_list_sum_err_temp)
            Prob_final_err[i_mu0, i_models]  = Prob_list_sum_err_temp / (Prob_list_sum_corr_temp + Prob_list_sum_err_temp)

        ## Analytical solutions (normalized) for simple DDM and CB_Linear, computed if they are in model_list
        if index_model_2use ==0 or index_model_2use==1:
            #note the temporary -ve sign for param_B_0...not sure if I still need it in exponential decay case etc...
            (Prob_list_corr_Analy_temp, Prob_list_err_Analy_temp) = DDM_pdf_analytical([mu_temp, sigma_0, param_mu_x_list[index_model_2use], B, -param_B_t_list[index_model_2use]], index_model_2use, 0) # Simple DDM
            Prob_list_sum_corr_Analy_temp  = np.sum(Prob_list_corr_Analy_temp)
            Prob_list_sum_err_Analy_temp   = np.sum(Prob_list_err_Analy_temp)
            Prob_list_sum_undec_Analy_temp = 1 - Prob_list_sum_corr_Analy_temp - Prob_list_sum_err_Analy_temp
            #Outputs...
            # Forced Choices: The monkey will always make a decision: Split the undecided probability half-half for corr/err choices. Actually don't think the analytical solution has undecided trials...
            Prob_final_undec_Analy[i_mu0, i_models] = Prob_list_sum_undec_Analy_temp
            Prob_final_corr_Analy[i_mu0, i_models]  = Prob_list_sum_corr_Analy_temp + Prob_final_undec_Analy[i_mu0, i_models]/2.
            Prob_final_err_Analy[i_mu0, i_models]   = Prob_list_sum_err_Analy_temp  + Prob_final_undec_Analy[i_mu0, i_models]/2.
            # Mean_Dec_Time_Analy[i_mu0, i_models]    = np.sum((Prob_list_corr_Analy_temp+Prob_list_err_Analy_temp) *t_list) / np.sum((Prob_list_corr_Analy_temp+Prob_list_err_Analy_temp))      # Regardless of choices. Note that Mean_Dec_Time does not includes choices supposedly undecided and made at the last moment.
            Mean_Dec_Time_Analy[i_mu0, i_models]    = np.sum((Prob_list_corr_Analy_temp)*t_list) / np.sum((Prob_list_corr_Analy_temp)) # Only consider correct choices. Note that Mean_Dec_Time does not includes choices supposedly undecided and made at the last moment.

    ## Compute the default models (based on spiking circuit) for the various models.
    (Prob_list_corr_0_temp, Prob_list_err_0_temp) = DDM_pdf_general([mu_0_list[0], param_mu_x_list[index_model_2use], param_mu_t_list[index_model_2use], sigma_0, param_sigma_x_list[index_model_2use], param_sigma_t_list[index_model_2use], B, param_B_t_list[index_model_2use]], index_model_2use, 0)                               # Simple DDM
    Prob_list_sum_corr_0_temp  = np.sum(Prob_list_corr_0_temp)
    Prob_list_sum_err_0_temp   = np.sum(Prob_list_err_0_temp)
    Prob_list_sum_undec_0_temp = 1. - Prob_list_sum_corr_0_temp - Prob_list_sum_err_0_temp
    #Outputs...
    Prob_final_corr_0[i_models]  = Prob_list_sum_corr_0_temp
    Prob_final_err_0[i_models]   = Prob_list_sum_err_0_temp
    Prob_final_undec_0[i_models] = Prob_list_sum_undec_0_temp
    Mean_Dec_Time_0[i_models]    = np.sum((Prob_list_corr_0_temp+Prob_list_err_0_temp) *t_list) / np.sum((Prob_list_corr_0_temp+Prob_list_err_0_temp))


### Plot correct probability, erred probability, indecision probability, and mean decision time.
fig1 = plt.figure(figsize=(8,10.5))
ax11 = fig1.add_subplot(411)
for i_models in range(len(models_list)):
    index_model_2use = models_list[i_models]
    ax11.plot(coh_list, Prob_final_corr[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    if index_model_2use ==0 or index_model_2use==1:
        ax11.plot(coh_list, Prob_final_corr_Analy[:,i_models], color=color_list[index_model_2use], linestyle=':') #, label=labels_list[index_model_2use]+"_A" )
#fig1.ylim([-1.,1.])
#ax11.set_xlabel('mu_0 (~coherence)')
ax11.set_ylabel('Probability')
ax11.set_title('Correct Probability')
# ax11.set_xscale('log')
ax11.legend(loc=4)

ax12 = fig1.add_subplot(412)
for i_models in range(len(models_list)):
    index_model_2use = models_list[i_models]
    ax12.plot(coh_list, Prob_final_err[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    if index_model_2use ==0 or index_model_2use==1:
        ax12.plot(coh_list, Prob_final_err_Analy[:,i_models], color=color_list[index_model_2use], linestyle=':') #, label=labels_list[index_model_2use]+"_A" )

#fig1.ylim([-1.,1.])
#ax12.set_xlabel('mu_0 (~coherence)')
ax12.set_ylabel('Probability')
ax12.set_title('Erred Probability')
# ax12.set_xscale('log')
ax12.legend(loc=1)


ax13 = fig1.add_subplot(413)
for i_models in range(len(models_list)):
    index_model_2use = models_list[i_models]
    ax13.plot(coh_list, Prob_final_undec[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    if index_model_2use ==0 or index_model_2use==1:
        ax13.plot(coh_list, Prob_final_undec_Analy[:,i_models], color=color_list[index_model_2use], linestyle=':') #, label=labels_list[index_model_2use]+"_A" )
#fig1.ylim([-1.,1.])
#ax13.set_xlabel('mu_0 (~coherence)')
ax13.set_ylabel('Probability')
ax13.set_title('Undecision Probability')
# ax13.set_xscale('log')
ax13.legend(loc=1)

ax14 = fig1.add_subplot(414)
for i_models in range(len(models_list)):
    index_model_2use = models_list[i_models]
    ax14.plot(coh_list, Mean_Dec_Time[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    if index_model_2use ==0 or index_model_2use==1:
        ax14.plot(coh_list, Mean_Dec_Time_Analy[:,i_models], color=color_list[index_model_2use], linestyle=':')        #, label=labels_list[index_model_2use]+"_A" )
#fig1.ylim([-1.,1.])
ax14.set_xlabel('Coherence (%)')
ax14.set_ylabel('Time (s)')
ax14.set_title('Mean Decision Time')
# ax14.set_xscale('log')
ax14.legend(loc=3)

fig1.savefig('Fixed_Task_Performance.pdf')
np.save( "fig3_c_x.npy", coh_list)   #Resave everytime, just to make sure I don't mess anything up..
np.save( "fig3_c_y.npy", Prob_final_corr)   #Resave everytime, just to make sure I don't mess anything up..
# mean time & indecision probabilitiies as SI?





########################################################################################################################
## Fig 2: compare analytical vs implicit method for simple DDM and Collapsing bound (linear). Others have no analytical forms.
if Flag_Compare_num_analy_sim:
    ###models_list_fig2 = [0,1] #List of models to use. See Setting_list (DDM and CB_Lin only here)
    mu_0_F2 = mu_0_list[-3] # Set a particular mu and play with variour settings...
    (Prob_list_corr_1_fig2     , Prob_list_err_1_fig2     ) = DDM_pdf_general(   [mu_0_F2, 0., 0., sigma_0, 0., 0., B, 0.], 0)
    (Prob_list_corr_1_Anal_fig2, Prob_list_err_1_Anal_fig2) = DDM_pdf_analytical([mu_0_F2        , sigma_0, 0.    , B, 0.], 0)
    (Prob_list_corr_2_fig2     , Prob_list_err_2_fig2     ) = DDM_pdf_general(   [mu_0_F2, 0., 0., sigma_0, 0., 0., B,  param_B_t ], 1)
    (Prob_list_corr_2_Anal_fig2, Prob_list_err_2_Anal_fig2) = DDM_pdf_analytical([mu_0_F2        , sigma_0, 0.    , B, -param_B_t], 1)
    (Prob_list_corr_3_fig2     , Prob_list_err_3_fig2     ) = DDM_pdf_general(   [mu_0_F2, 0., 0., sigma_0, 0., 0., B,  param_B_t, T_dur/4. ], 0, 3)
    (Prob_list_corr_4_fig2     , Prob_list_err_4_fig2     ) = DDM_pdf_general(   [mu_0_F2, 0., 0., sigma_0, 0., 0., B,  param_B_t, T_dur/4. ], 1, 3)


    # Cumulative Sums
    Prob_list_cumsum_corr_1_fig2  = np.cumsum(Prob_list_corr_1_fig2)
    Prob_list_cumsum_err_1_fig2  = np.cumsum(Prob_list_err_1_fig2)
    Prob_list_cumsum_corr_1_Anal_fig2  = np.cumsum(Prob_list_corr_1_Anal_fig2)
    Prob_list_cumsum_err_1_Anal_fig2  = np.cumsum(Prob_list_err_1_Anal_fig2)
    Prob_list_cumsum_corr_2_fig2  = np.cumsum(Prob_list_corr_2_fig2)
    Prob_list_cumsum_err_2_fig2  = np.cumsum(Prob_list_err_2_fig2)
    Prob_list_cumsum_corr_2_Anal_fig2  = np.cumsum(Prob_list_corr_2_Anal_fig2)
    Prob_list_cumsum_err_2_Anal_fig2  = np.cumsum(Prob_list_err_2_Anal_fig2)
    Prob_list_cumsum_corr_3_fig2  = np.cumsum(Prob_list_corr_3_fig2)
    Prob_list_cumsum_err_3_fig2  = np.cumsum(Prob_list_err_3_fig2)
    Prob_list_cumsum_corr_4_fig2  = np.cumsum(Prob_list_corr_4_fig2)
    Prob_list_cumsum_err_4_fig2  = np.cumsum(Prob_list_err_4_fig2)


    # In case the trial model has no analytical solution, use simulation (see DDM_sim_compare_pdf.py) instead.
    [bins_edge_t_correct_sim_temp, pdf_t_correct_sim_temp, bins_edge_t_incorrect_sim_temp, pdf_t_incorrect_sim_temp] = np.load('DDM_sim_t_pdf.npy')
    bins_t_correct_sim_temp = 0.5*(bins_edge_t_correct_sim_temp[1:] + bins_edge_t_correct_sim_temp[:-1])
    bins_t_incorrect_sim_temp = 0.5*(bins_edge_t_incorrect_sim_temp[1:] + bins_edge_t_incorrect_sim_temp[:-1])
    norm_sim_temp = np.sum(pdf_t_correct_sim_temp + pdf_t_incorrect_sim_temp)
    dt_ratio = 10. # Ratio in time step, and thus 1/ number of datapoints, between simulation and numerical solutions.


    ### Plot correct probability, erred probability, indecision probability, and mean decision time.
    fig2 = plt.figure(figsize=(8,10.5))
    ax21 = fig2.add_subplot(411) # PDF, Correct
    ax21.plot(t_list, Prob_list_corr_1_fig2, 'r', label='DDM' )
    ax21.plot(t_list, Prob_list_corr_1_Anal_fig2, 'r:', label='DDM_A' )
    ax21.plot(t_list, Prob_list_corr_2_fig2, 'b', label='test' )
    ax21.plot(t_list, Prob_list_corr_2_fig2, 'b', label='CB_Lin' )
    ax21.plot(t_list, Prob_list_corr_2_Anal_fig2, 'b:', label='CB_Lin_A' )
    ax21.plot(t_list, Prob_list_corr_3_fig2, 'r--', label='DDM_P' )
    ax21.plot(t_list, Prob_list_corr_4_fig2, 'b--', label='CB_Lin_P' )
    ## ax21.plot(bins_t_correct_sim_temp, pdf_t_correct_sim_temp/dt_ratio, 'k-.', label='sim' )
    #fig1.ylim([-1.,1.])
    ax21.set_xlabel('time (s)')
    ax21.set_ylabel('PDF (normalized)')
    ax21.set_title('Correct PDF, Analytical vs Numerical')
    # ax21.set_xscale('log')
    ax21.legend(loc=1)

    ax22 = fig2.add_subplot(412) # PDF, erred
    ax22.plot(t_list, Prob_list_err_1_fig2, 'r', label='DDM' )
    ax22.plot(t_list, Prob_list_err_1_Anal_fig2, 'r:', label='DDM_A' )
    ax22.plot(t_list, Prob_list_err_2_fig2, 'b', label='test' )
    ax22.plot(t_list, Prob_list_err_2_fig2, 'b', label='CB_Lin' )
    ax22.plot(t_list, Prob_list_err_2_Anal_fig2, 'b:', label='CB_Lin_A' )
    ax22.plot(t_list, Prob_list_err_3_fig2, 'r--', label='DDM_P' )
    ax22.plot(t_list, Prob_list_err_4_fig2, 'b--', label='CB_Lin_P' )
    ## ax22.plot(bins_t_incorrect_sim_temp, pdf_t_incorrect_sim_temp/dt_ratio, 'k-.', label='sim' )
    #fig1.set_ylim([-1.,1.])
    ax22.set_xlabel('time (s)')
    ax22.set_ylabel('PDF (normalized)')
    ax22.set_title('Erred PDF, Analytical vs Numerical')
    # fig1.set_xscale('log')
    ax22.legend(loc=1)

    ax23 = fig2.add_subplot(413) # CDF, Correct
    ax23.plot(t_list, Prob_list_cumsum_corr_1_fig2, 'r', label='DDM' )
    ax23.plot(t_list, Prob_list_cumsum_corr_1_Anal_fig2, 'r:', label='DDM_A' )
    ax23.plot(t_list, Prob_list_cumsum_corr_2_fig2, 'b', label='test' )
    ax23.plot(t_list, Prob_list_cumsum_corr_2_fig2, 'b', label='CB_Lin' )
    ax23.plot(t_list, Prob_list_cumsum_corr_2_Anal_fig2, 'b:', label='CB_Lin_A' )
    ax23.plot(t_list, Prob_list_cumsum_corr_3_fig2, 'r--', label='DDM_P' )
    ax23.plot(t_list, Prob_list_cumsum_corr_4_fig2, 'b--', label='CB_Lin_P' )
    ## ax23.plot(bins_t_correct_sim_temp, np.cumsum(pdf_t_correct_sim_temp), 'k-.', label='sim' )

    #fig1.ylim([-1.,1.])
    ax23.set_xlabel('time (s)')
    ax23.set_ylabel('CDF (normalized)')
    ax23.set_title('Correct CDF, Analytical vs Numerical')
    # ax23.set_xscale('log')
    ax23.legend(loc=4)

    ax24 = fig2.add_subplot(414) # CDF, Erred
    ax24.plot(t_list, Prob_list_cumsum_err_1_fig2, 'r', label='DDM' )
    ax24.plot(t_list, Prob_list_cumsum_err_1_Anal_fig2, 'r:', label='DDM_A' )
    ax24.plot(t_list, Prob_list_cumsum_err_2_fig2, 'b', label='test' )
    ax24.plot(t_list, Prob_list_cumsum_err_2_fig2, 'b', label='CB_Lin' )
    ax24.plot(t_list, Prob_list_cumsum_err_2_Anal_fig2, 'b:', label='CB_Lin_A' )
    ax24.plot(t_list, Prob_list_cumsum_err_3_fig2, 'r--', label='DDM_P' )
    ax24.plot(t_list, Prob_list_cumsum_err_4_fig2, 'b--', label='CB_Lin_P' )
    ## ax24.plot(bins_t_incorrect_sim_temp, np.cumsum(pdf_t_incorrect_sim_temp), 'k-.', label='sim' )
    #fig1.set_ylim([-1.,1.])
    ax24.set_xlabel('time (s)')
    ax24.set_ylabel('CDF (normalized)')
    ax24.set_title('Erred CDF, Analytical vs Numerical')
    # fig1.set_xscale('log')
    ax24.legend(loc=4)

    fig2.savefig('Numerical_vs_Analytical_DDM_CBLin.pdf')



















########################################################################################################################
# NOTE: ALL BELOW CAN BE DELETED IF IRREVLEVENT. Only left here coz

### Psychophysical Kernel/ Duration Paradigm/ Pulse Paradigm...
# Pulse Paradigm...

if Flag_Pulse:
    t_onset_list_pulse = np.arange(0., T_dur, 0.1)
    models_list = [0,3,4]                                #List of models to use. See Setting_list
    models_list = [0,1,2,3,4]                                #List of models to use. See Setting_list

    Prob_final_corr_pulse  = np.zeros((len(t_onset_list_pulse), len(mu_0_list), len(models_list)))
    Prob_final_err_pulse   = np.zeros((len(t_onset_list_pulse), len(mu_0_list), len(models_list)))
    Prob_final_undec_pulse = np.zeros((len(t_onset_list_pulse), len(mu_0_list), len(models_list)))
    Mean_Dec_Time_pulse    = np.zeros((len(t_onset_list_pulse), len(mu_0_list), len(models_list)))


    ## For each models, find the probability to be correct/erred/undec for various mu and t_onset_pulse
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        for i_mu0 in range(len(mu_0_list)):
            mu_2use = mu_0_list[i_mu0]
            for i_ton in range(len(t_onset_list_pulse)):
                t_onset_temp = t_onset_list_pulse[i_ton]
                (Prob_list_corr_pulse_temp, Prob_list_err_pulse_temp) = DDM_pdf_general([mu_2use, param_mu_x_list[index_model_2use], param_mu_t_list[index_model_2use], sigma_0, param_sigma_x_list[index_model_2use], param_sigma_t_list[index_model_2use], B, param_B_t_list[index_model_2use], t_onset_temp], index_model_2use, 3)                               # Simple DDM
                Prob_list_sum_corr_pulse_temp = np.sum(Prob_list_corr_pulse_temp)
                Prob_list_sum_err_pulse_temp  = np.sum(Prob_list_err_pulse_temp)

                Prob_list_sum_undec_pulse_temp  = 1. - Prob_list_sum_corr_pulse_temp - Prob_list_sum_err_pulse_temp

                #Outputs...
                Prob_final_undec_pulse[i_ton, i_mu0, i_models] = Prob_list_sum_undec_pulse_temp
                Prob_final_corr_pulse[i_ton, i_mu0, i_models]  = Prob_list_sum_corr_pulse_temp + Prob_final_undec_pulse[i_ton, i_mu0, i_models]/2.
                Prob_final_err_pulse[i_ton, i_mu0, i_models]   = Prob_list_sum_err_pulse_temp  + Prob_final_undec_pulse[i_ton, i_mu0, i_models]/2.
                # Mean_Dec_Time_pulse[i_ton, i_mu0, i_models]    = np.sum((Prob_list_corr_pulse_temp+Prob_list_err_pulse_temp) *t_list) / np.sum((Prob_list_corr_pulse_temp+Prob_list_err_pulse_temp))        # Regardless of choices. Note that Mean_Dec_Time does not includes choices supposedly undecided and made at the last moment.
                Mean_Dec_Time_pulse[i_ton, i_mu0, i_models]    = np.sum((Prob_list_corr_pulse_temp)*t_list) / np.sum((Prob_list_corr_pulse_temp))                                                           # Only correct choices. Note that Mean_Dec_Time does not includes choices supposedly undecided and made at the last moment.

                ##Temp:
                # if index_model_2use ==1:
                #     Prob_final_corr_pulse[i_ton, i_models] = Prob_list_cumsum_corr_pulse_temp[-1] / (Prob_list_cumsum_corr_pulse_temp[-1] + Prob_list_cumsum_err_pulse_temp[-1])
                #     Prob_final_err_pulse[i_ton, i_models]  = Prob_list_cumsum_err_pulse_temp[-1] / (Prob_list_cumsum_corr_pulse_temp[-1] + Prob_list_cumsum_err_pulse_temp[-1])


    ## For each model and each t_onset_pulse, fit the psychometric function
    psychometric_params_list_pulse = np.zeros((3 , len(t_onset_list_pulse), len(models_list))) # Note that params_pm in Psychometric_fit_P has only 2 fit parameters...
    param_fit_0_pulse = [2. ,1., 0.] # Temp, initial guess for param_pm for Psychometric_fit_P.
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        for i_ton in range(len(t_onset_list_pulse)):
            t_onset_temp = t_onset_list_pulse[i_ton]
            res_temp = minimize(Psychometric_fit_P, param_fit_0_pulse, args = ([Prob_final_corr_pulse[i_ton,:,i_models]]))     #Note that mu_0_list is intrinsically defined in the Psychometric_fit_P function
            psychometric_params_list_pulse[:,i_ton,i_models] = res_temp.x




    figP = plt.figure(figsize=(8,10.5))
    axP1 = figP.add_subplot(411)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axP1.plot(t_onset_list_pulse, psychometric_params_list_pulse[2,:,i_models]*100./mu_0, color=color_list[index_model_2use], label=labels_list[index_model_2use] )               # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
        # axP1.axhline(Prob_final_corr_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    #figP.ylim([-1.,1.])
    #axP1.set_xlabel('mu_0 (~coherence)')
    axP1.set_ylabel('Shift')
    axP1.set_title('Psychometric function Shift')
    # axP1.set_xscale('log')
    axP1.legend(loc=1)

    axP2 = figP.add_subplot(412)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axP2.plot(t_onset_list_pulse, psychometric_params_list_pulse[0,:,i_models]*100./mu_0, color=color_list[index_model_2use], label=labels_list[index_model_2use] )               # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
        # axP2.axhline(Prob_final_corr_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    #figP.ylim([-1.,1.])
    #axP2.set_xlabel('mu_0 (~coherence)')
    axP2.set_ylabel('Threshold')
    axP2.set_title('Psychometric function Threshold')
    # axP2.set_xscale('log')
    axP2.legend(loc=1)

    axP3 = figP.add_subplot(413)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axP3.plot(t_onset_list_pulse, psychometric_params_list_pulse[1,:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
        # axP3.axhline(Prob_final_err_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    #figP.ylim([-1.,1.])
    #axP3.set_xlabel('mu_0 (~coherence)')
    axP3.set_ylabel('Order')
    axP3.set_title('Psychometric function Slope/Order')
    # axP3.set_xscale('log')
    axP2.legend(loc=4)

    axP4 = figP.add_subplot(414)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axP4.plot(mu_0_list, Prob_final_corr[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
#        axP4.plot(mu_0_list, 1./(1.+ np.exp(-psychometric_params_list_pulse[1,0,i_models]*(mu_0_list+psychometric_params_list_pulse[0,0,i_models]))), color=color_list[index_model_2use], label=labels_list[index_model_2use], linestyle=":" )
        axP4.plot(mu_0_list, Prob_final_corr_pulse[-1,:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use], linestyle="--" )
        # axP4.plot(mu_0_list, 1./(1.+ np.exp(-psychometric_params_list_pulse[1,-1,i_models]*(mu_0_list+psychometric_params_list_pulse[0,-1,i_models]))), color=color_list[index_model_2use], label=labels_list[index_model_2use], linestyle=":" )
        axP4.plot(mu_0_list, 0.5 + np.sign(mu_0_list)*0.5*(1. - np.exp(-(np.sign(mu_0_list)*(mu_0_list+psychometric_params_list_pulse[2,-1,i_models])/psychometric_params_list_pulse[0,-1,i_models]) **psychometric_params_list_pulse[1,-1,i_models])) , color=color_list[index_model_2use], label=labels_list[index_model_2use]+'_long' , linestyle=":" )
# axP4.axhline(Prob_final_err_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    #figP.ylim([-1.,1.])
    #axP2.set_xlabel('mu_0 (~coherence)')
    axP4.set_ylabel('Correct Probability')
    axP4.set_title('Correct Probability')
    # axP4.set_xscale('log')
    axP4.legend(loc=4)


    # axP3 = figP.add_subplot(413)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axP3.plot(t_onset_list_pulse, Prob_final_undec_pulse[:,i_mu0_2plot,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    #     axP3.axhline(Prob_final_undec_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # #figP.ylim([-1.,1.])
    # #axP3.set_xlabel('mu_0 (~coherence)')
    # axP3.set_ylabel('Probability')
    # axP3.set_title('Undecision Probability')
    # # axP3.set_xscale('log')
    # axP3.legend(loc=1)
    #
    # axP4 = figP.add_subplot(414)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axP4.plot(t_onset_list_pulse, Mean_Dec_Time_pulse[:,i_mu0_2plot,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    #     axP4.axhline(Mean_Dec_Time_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # #figP.ylim([-1.,1.])
    # axP4.set_xlabel('Pulse Onset Time (s)')
    # axP4.set_ylabel('Time (s)')
    # axP4.set_title('Mean Decision Time')
    # # axP4.set_xscale('log')
    # axP4.legend(loc=3)

    figP.savefig('Pulse_paradigm.pdf')

    np.save( "fig3_e_x.npy", t_onset_list_pulse)   #Resave everytime, just to make sure I don't mess anything up..
    np.save( "fig3_e_y.npy", psychometric_params_list_pulse[2,:,:]*100./mu_0)   #Resave everytime, just to make sure I don't mess anything up..
    # Not sure if we want to show sample psychoimetric functions and its shifts...if so can quite easily add...







    # figPn = plt.figure(figsize=(8,10.5))
    # axPn1 = figPn.add_subplot(411)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axPn1.plot(t_onset_list_pulse, (Prob_final_corr_pulse[:,i_models]-Prob_final_corr_0[index_model_2use])/np.max(np.abs(Prob_final_corr_pulse[:,i_models]-Prob_final_corr_0[index_model_2use])), color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #figPn.ylim([-1.,1.])
    # #axPn1.set_xlabel('mu_0 (~coherence)')
    # #axPn1.axhline(0.5, color='k', linestyle="--")
    # axPn1.set_ylim([-1., 1.])
    # axPn1.set_ylabel('Probability')
    # axPn1.set_title('Correct Probability, Norm')
    # # axPn1.set_xscale('log')
    # axPn1.legend(loc=4)
    #
    # axPn2 = figPn.add_subplot(412)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axPn2.plot(t_onset_list_pulse, (Prob_final_err_pulse[:,i_models]-Prob_final_err_0[index_model_2use])/np.max(np.abs(Prob_final_err_pulse[:,i_models]-Prob_final_err_0[index_model_2use])), color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #figPn.ylim([-1.,1.])
    # #axPn2.set_xlabel('mu_0 (~coherence)')
    # #axPn2.axhline(0.5, color='k', linestyle="--")
    # axPn2.set_ylim([-1., 1.])
    # axPn2.set_ylabel('Probability')
    # axPn2.set_title('Erred Probability')
    # # axPn2.set_xscale('log')
    # axPn2.legend(loc=4)
    #
    #
    # axPn3 = figPn.add_subplot(413)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axPn3.plot(t_onset_list_pulse, (Prob_final_undec_pulse[:,i_models]-Prob_final_undec_0[index_model_2use])/np.max(np.abs(Prob_final_undec_pulse[:,i_models]-Prob_final_undec_0[index_model_2use])), color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #figPn.ylim([-1.,1.])
    # #axPn3.set_xlabel('mu_0 (~coherence)')
    # #axPn3.axhline(0.5, color='k', linestyle="--")
    # axPn3.set_ylim([-1., 1.])
    # axPn3.set_ylabel('Probability')
    # axPn3.set_title('Undecision Probability')
    # # axPn3.set_xscale('log')
    # axPn3.legend(loc=1)
    #
    # axPn4 = figPn.add_subplot(414)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axPn4.plot(t_onset_list_pulse, (Mean_Dec_Time_pulse[:,i_models]-Mean_Dec_Time_0[index_model_2use])/np.max(np.abs(Mean_Dec_Time_pulse[:,i_models]-Mean_Dec_Time_0[index_model_2use])), color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #figPn.ylim([-1.,1.])
    # #axPn4.axhline(0.5, color='k', linestyle="--")
    # axPn4.set_ylim([-1., 1.])
    # axPn4.set_xlabel('Pulse Onset Time (s)')
    # axPn4.set_ylabel('Time (s)')
    # axPn4.set_title('Mean Decision Time')
    # # axPn4.set_xscale('log')
    # axPn4.legend(loc=3)
    #
    # figPn.savefig('Pulse_paradigm_norm.pdf')



########################################################################################################################
# Duration Paradigm...
if Flag_Duration:
    # t_dur_list_duration = np.arange(0.05, T_dur+0.01, 0.05)
    t_dur_list_duration = np.arange(0.1, T_dur+0.01, 0.1)
    # t_dur_list_duration_2 = np.arange(0.2, 0.5+0.01, 0.05)
    # t_dur_list_duration   = sorted(set(np.concatenate((t_dur_list_duration_1,t_dur_list_duration_2),axis=0)))		#To create an array/ parameter scale of varying densities

    models_list = [0,3,4] # List of models to use. See Setting_list
    # models_list = models_list_all # List of models to use. See Setting_list
    coh_skip_threshold = 60. # Threshold value above which data is skipped.
    n_skip_fit_list = np.zeros(len(models_list)).astype(int) # Only integer skips                                                                        # Define the number of skipped data based on coh_skip_threshold later on.


    Prob_final_corr_duration  = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(models_list)))
    Prob_final_err_duration   = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(models_list)))
    Prob_final_undec_duration = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(models_list)))
    Mean_Dec_Time_duration    = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(models_list)))




    ## For each models, find the probability to be correct/erred/undec for various mu and t_onset_pulse
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        for i_mu0 in range(len(mu_0_list)):
            mu_2use = mu_0_list[i_mu0]
            for i_tdur in range(len(t_dur_list_duration)):
                t_dur_temp = t_dur_list_duration[i_tdur]
                #t_list_temp = np.arange(0., t_dur_temp, dt) # If cutoff time at the end of stimulus (T_dur)
                t_list_temp = t_list # If cutoff time is constant/ indep of T_dur
                (Prob_list_corr_duration_temp, Prob_list_err_duration_temp) = DDM_pdf_general([mu_2use, param_mu_x_list[index_model_2use], param_mu_t_list[index_model_2use], sigma_0, param_sigma_x_list[index_model_2use], param_sigma_t_list[index_model_2use], B, param_B_t_list[index_model_2use], t_dur_temp], index_model_2use, 2)                               # Simple DDM
                Prob_list_sum_corr_duration_temp  = np.sum(Prob_list_corr_duration_temp)
                Prob_list_sum_err_duration_temp   = np.sum(Prob_list_err_duration_temp)
                Prob_list_sum_undec_duration_temp = 1. - Prob_list_sum_corr_duration_temp - Prob_list_sum_err_duration_temp

                #Outputs...
                Prob_final_undec_duration[i_tdur, i_mu0, i_models] = Prob_list_sum_undec_duration_temp
                Prob_final_corr_duration[i_tdur, i_mu0, i_models]  = Prob_list_sum_corr_duration_temp + Prob_final_undec_duration[i_tdur, i_mu0, i_models]/2.
                Prob_final_err_duration[i_tdur, i_mu0, i_models]   = Prob_list_sum_err_duration_temp  + Prob_final_undec_duration[i_tdur, i_mu0, i_models]/2.
                Mean_Dec_Time_duration[i_tdur, i_mu0, i_models]    = np.sum((Prob_list_corr_duration_temp+Prob_list_err_duration_temp) *t_list_temp) / np.sum((Prob_list_corr_duration_temp+Prob_list_err_duration_temp))

                ##Temp:
                # if index_model_2use ==1:
                #     Prob_final_corr_duration[i_tdur, i_models] = Prob_list_sum_corr_duration_temp / (Prob_list_sum_corr_duration_temp + Prob_list_sum_err_duration_temp)
                #     Prob_final_err_duration[i_tdur, i_models]  = Prob_list_sum_err_duration_temp / (Prob_list_sum_corr_duration_temp + Prob_list_sum_err_duration_temp)

    ## For each model and each t_dur_duration, fit the psychometric function
    psychometric_params_list_duration = np.zeros((2 , len(t_dur_list_duration), len(models_list))) # Note that params_pm in Psychometric_fit has only 2 fit parameters...
    param_fit_0_duration = [2.,0.5] # Temp, initial guess for param_pm for Psychometric_fit_D.
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        for i_tdur in range(len(t_dur_list_duration)):
            t_dur_temp = t_dur_list_duration[i_tdur]
            res_temp = minimize(Psychometric_fit_D, param_fit_0_duration, args = ([Prob_final_corr_duration[i_tdur,:,i_models]])) #Note that mu_0_list is intrinsically defined in the Psychometric_fit function
            psychometric_params_list_duration[:,i_tdur,i_models] = res_temp.x

        n_skip_fit_list[i_models] = int(np.sum( psychometric_params_list_duration[0,:,i_models]*100./mu_0  > coh_skip_threshold)) # First define which how many terms in the pscyhomeric_params_list to skip/ not include in fit. All data that has threshold >100% is removed.


    ## Fit Psychometric Threshold with a decaying exponential + Constant
    # Note that we would want to change varaibles_list at the top, to do a scan of OU-parameters
    param_fit_threshold_duration = [15., 0.2, 0., 100.] # Temp, initial guess for param_pm for Psychometric_fit_D.
    threshold_fit_params_list_duration = np.zeros((len(param_fit_threshold_duration), len(models_list))) # Note that params_pm in Psychometric_fit has only 2 fit parameters...
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        res_temp_threshold = minimize(Threshold_D_fit, param_fit_threshold_duration, args = (psychometric_params_list_duration[0,:,i_models]*100./mu_0, n_skip_fit_list[i_models], t_dur_list_duration)) #Note that mu_0_list is intrinsically defined in the Psychometric_fit function
        threshold_fit_params_list_duration[:,i_models] = res_temp_threshold.x

    # print threshold_fit_params_list_duration[0, i_models] + (100.-threshold_fit_params_list_duration[0, i_models])*(np.exp(-((t_dur_list_duration-threshold_fit_params_list_duration[2, i_models])/threshold_fit_params_list_duration[1, i_models])))


    figD = plt.figure(figsize=(8,10.5))
    axD1 = figD.add_subplot(311)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axD1.plot(t_dur_list_duration, psychometric_params_list_duration[0,:,i_models]*100./mu_0, color=color_list[index_model_2use], label=labels_list[index_model_2use] )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
        axD1.plot(t_dur_list_duration, threshold_fit_params_list_duration[0, i_models] + (threshold_fit_params_list_duration[3, i_models])*(np.exp(-((t_dur_list_duration-threshold_fit_params_list_duration[2, i_models])/threshold_fit_params_list_duration[1, i_models]))), color=color_list[index_model_2use], label=labels_list[index_model_2use], linestyle="--" )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
#         axD1.plot(t_dur_list_duration, threshold_fit_params_list_duration[0, i_models] + (100.-threshold_fit_params_list_duration[0, i_models])*(np.exp(-((t_dur_list_duration-threshold_fit_params_list_duration[2, i_models])/threshold_fit_params_list_duration[1, i_models])**threshold_fit_params_list_duration[3, i_models])), color=color_list[index_model_2use], label=labels_list[index_model_2use], linestyle="--" )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    #    axD1.axhline(Prob_final_corr_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # axD1.set_ylim([10.,100.])
    axD1.set_xlabel('Stimulation Duration (s)')
    axD1.set_ylabel('Threshold')
    axD1.set_title('Psychometric function Decision Threshold')
    # axD1.set_yscale('log')
    axD1.legend(loc=1)

    axD2 = figD.add_subplot(312)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axD2.plot(t_dur_list_duration, psychometric_params_list_duration[1,:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    #    axD2.axhline(Prob_final_err_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    #figD.ylim([-1.,1.])
    #axD2.set_xlabel('mu_0 (~coherence)')
    # axD2.set_ylim([1.,5.])
    axD2.set_ylabel('Order')
    # axD2.set_title('Psychometric function Beta')
    # axD2.set_yscale('log')
    axD2.legend(loc=1)

    axD3 = figD.add_subplot(313)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axD3.plot(coh_list, Prob_final_corr_duration[0,  :, i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use]+'_short' )
        axD3.plot(coh_list, Prob_final_corr_duration[-1, :, i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use]+'_long' , linestyle=":" )
        axD3.plot(coh_list, 0.5 + 0.5*(1. - np.exp(-(mu_0_list/psychometric_params_list_duration[0,0,i_models]) **psychometric_params_list_duration[1,0,i_models])) , color=color_list[index_model_2use], linestyle="--")#, label=labels_list[index_model_2use]+'_short_F')
        axD3.plot(coh_list, 0.5 + 0.5*(1. - np.exp(-(mu_0_list/psychometric_params_list_duration[0,-1,i_models])**psychometric_params_list_duration[1,-1,i_models])), color=color_list[index_model_2use], linestyle="-.")#, label=labels_list[index_model_2use]+'_long_F' )
        # axP3.axhline(Prob_final_err_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    #figP.ylim([-1.,1.])
    #axP2.set_xlabel('mu_0 (~coherence)')
    axD3.set_xlabel('Coherence')
    axD3.set_ylabel('Probability')
    axD3.set_title('Correct Probability')
    # axP2.set_xscale('log')
    axD3.legend(loc=4)

    # axD3 = figD.add_subplot(413)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axD3.plot(t_dur_list_duration, Prob_final_undec_duration[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #    axD3.axhline(Prob_final_undec_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # #figD.ylim([-1.,1.])
    # #axD3.set_xlabel('mu_0 (~coherence)')
    # axD3.set_ylabel('Probability')
    # axD3.set_title('Undecision Probability')
    # # axD3.set_xscale('log')
    # axD3.legend(loc=1)
    #
    # axD4 = figD.add_subplot(414)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axD4.plot(t_dur_list_duration, Mean_Dec_Time_duration[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #    axD4.axhline(Mean_Dec_Time_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # #figD.ylim([-1.,1.])
    # axD4.set_xlabel('Duration (s)')
    # axD4.set_ylabel('Time (s)')
    # axD4.set_title('Mean Decision Time')
    # # axD4.set_xscale('log')
    # axD4.legend(loc=3)

    figD.savefig('Duration_paradigm.pdf')
    np.save( "fig3_f_x.npy", t_dur_list_duration)   #Resave everytime, just to make sure I don't mess anything up..
    np.save( "fig3_f_y.npy", psychometric_params_list_duration[0,:,:]*100./mu_0)   #Resave everytime, just to make sure I don't mess anything up..

    # figD_params = plt.figure(figsize=(8,10.5))
    # axD_params1 = figD_params.add_subplot(211)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axD_params1.plot(threshold_fit_params_list_duration[1, i_models], threshold_fit_params_list_duration[0, i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use], marker="x")         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    # #    axD_params1.axhline(Prob_final_corr_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # # axD_params1.set_ylim([10.,100.])
    # axD_params1.set_xlabel('Stimulation Duration (s)')
    # axD_params1.set_ylabel('Threshold')
    # axD_params1.set_title('Psychometric function Decision Threshold')
    # # axD_params1.set_yscale('log')
    # axD_params1.legend(loc=4)
    #
    #
    #
    # figD_params.savefig('Duration_paradigm_params_scan.pdf')


############################################################    # Redo Param scan with a range of OU parameters


    # OU_pos_range = np.arange(0.1*param_mu_x_OUpos,1.55*param_mu_x_OUpos, 0.1*param_mu_x_OUpos)
    OU_pos_range = [0.1*param_mu_x_OUpos,0.6*param_mu_x_OUpos, 1.*param_mu_x_OUpos, 1.5*param_mu_x_OUpos, 2.0*param_mu_x_OUpos]
#     OU_neg_range_1 = np.arange(0.1*param_mu_x_OUneg,1.55*param_mu_x_OUneg, 0.1*param_mu_x_OUneg)
# #    OU_neg_range_2 = np.arange(0.02*param_mu_x_OUneg,0.2*param_mu_x_OUneg, 0.02*param_mu_x_OUneg)
#     OU_neg_range_2 = [0.0001*param_mu_x_OUneg,0.001*param_mu_x_OUneg, 0.01*param_mu_x_OUneg]
#     OU_neg_range = sorted(set(np.concatenate((OU_neg_range_1,OU_neg_range_2),axis=0)))		#To create an array/ parameter scale of varying densities
    OU_neg_range = [0.5*param_mu_x_OUneg,0.8*param_mu_x_OUneg, 1.*param_mu_x_OUneg, 1.2*param_mu_x_OUneg]


    Prob_final_corr_duration_scan_OUpos  = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_pos_range)))
    Prob_final_err_duration_scan_OUpos   = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_pos_range)))
    Prob_final_undec_duration_scan_OUpos = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_pos_range)))
    Mean_Dec_Time_duration_scan_OUpos    = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_pos_range)))
    Prob_final_corr_duration_scan_OUneg  = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_neg_range)))
    Prob_final_err_duration_scan_OUneg   = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_neg_range)))
    Prob_final_undec_duration_scan_OUneg = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_neg_range)))
    Mean_Dec_Time_duration_scan_OUneg    = np.zeros((len(t_dur_list_duration), len(mu_0_list), len(OU_neg_range)))

    index_model_OUpos = 3
    index_model_OUneg = 4

    ## For each models, find the probability to be correct/erred/undec for various mu and t_onset_pulse
    for i_OUpos in range(len(OU_pos_range)):
        OU_param_2use = OU_pos_range[i_OUpos]
        for i_mu0 in range(len(mu_0_list)):
            mu_2use = mu_0_list[i_mu0]
            for i_tdur in range(len(t_dur_list_duration)):
                t_dur_temp = t_dur_list_duration[i_tdur]
                # t_list_temp = np.arange(0., t_dur_temp, dt) # If cutoff time at the end of stimulus (T_dur)
                t_list_temp = t_list # If cutoff time is constant/ indep of T_dur
                (Prob_list_corr_duration_temp, Prob_list_err_duration_temp) = DDM_pdf_general([mu_2use, OU_param_2use, param_mu_t_list[index_model_OUpos], sigma_0, param_sigma_x_list[index_model_OUpos], param_sigma_t_list[index_model_OUpos], B, param_B_t_list[index_model_OUpos], t_dur_temp], index_model_OUpos, 2)                               # Simple DDM
                Prob_list_sum_corr_duration_temp = np.sum(Prob_list_corr_duration_temp)
                Prob_list_sum_err_duration_temp  = np.sum(Prob_list_err_duration_temp)

                Prob_list_sum_undec_duration_temp  = 1. - Prob_list_sum_corr_duration_temp - Prob_list_sum_err_duration_temp

                # Outputs...
                Prob_final_undec_duration_scan_OUpos[i_tdur, i_mu0, i_OUpos] = Prob_list_sum_undec_duration_temp
                Prob_final_corr_duration_scan_OUpos[i_tdur, i_mu0, i_OUpos]  = Prob_list_sum_corr_duration_temp + Prob_list_sum_undec_duration_temp/2.
                Prob_final_err_duration_scan_OUpos[i_tdur, i_mu0, i_OUpos]   = Prob_list_sum_err_duration_temp  + Prob_list_sum_undec_duration_temp/2.
                Mean_Dec_Time_duration_scan_OUpos[i_tdur, i_mu0, i_OUpos]    = np.sum((Prob_list_corr_duration_temp+Prob_list_err_duration_temp) *t_list_temp) / np.sum((Prob_list_corr_duration_temp+Prob_list_err_duration_temp))
    for i_OUneg in range(len(OU_neg_range)):
        OU_param_2use = OU_neg_range[i_OUneg]
        for i_mu0 in range(len(mu_0_list)):
            mu_2use = mu_0_list[i_mu0]
            for i_tdur in range(len(t_dur_list_duration)):
                t_dur_temp = t_dur_list_duration[i_tdur]
                #t_list_temp = np.arange(0., t_dur_temp, dt) # If cutoff time at the end of stimulus (T_dur)
                t_list_temp = t_list # If cutoff time is constant/ indep of T_dur
                (Prob_list_corr_duration_temp, Prob_list_err_duration_temp) = DDM_pdf_general([mu_2use, OU_param_2use, param_mu_t_list[index_model_OUneg], sigma_0, param_sigma_x_list[index_model_OUneg], param_sigma_t_list[index_model_OUneg], B, param_B_t_list[index_model_OUpos], t_dur_temp], index_model_OUneg, 2)                               # Simple DDM
                Prob_list_sum_corr_duration_temp  = np.sum(Prob_list_corr_duration_temp)
                Prob_list_sum_err_duration_temp  = np.sum(Prob_list_err_duration_temp)
                Prob_list_sum_undec_duration_temp  = 1. - Prob_list_sum_corr_duration_temp - Prob_list_sum_err_duration_temp

                #Outputs...
                Prob_final_undec_duration_scan_OUneg[i_tdur, i_mu0, i_OUneg] = Prob_list_sum_undec_duration_temp
                Prob_final_corr_duration_scan_OUneg[i_tdur, i_mu0, i_OUneg]  = Prob_list_sum_corr_duration_temp + Prob_list_sum_undec_duration_temp/2.
                Prob_final_err_duration_scan_OUneg[i_tdur, i_mu0, i_OUneg]   = Prob_list_sum_err_duration_temp  + Prob_list_sum_undec_duration_temp/2.
                Mean_Dec_Time_duration_scan_OUneg[i_tdur, i_mu0, i_OUneg]    = np.sum((Prob_list_corr_duration_temp+Prob_list_err_duration_temp) *t_list_temp) / np.sum((Prob_list_corr_duration_temp+Prob_list_err_duration_temp))



    ## For each model and each t_dur_duration, fit the psychometric function
    param_fit_0_duration = [2.,0.5] # Temp, initial guess for param_pm for Psychometric_fit_D.
    psychometric_params_list_duration_scan_OUpos = np.zeros((2 , len(t_dur_list_duration), len(OU_pos_range))) # Note that params_pm in Psychometric_fit has only 2 fit parameters...
    psychometric_params_list_duration_scan_OUneg = np.zeros((2 , len(t_dur_list_duration), len(OU_neg_range))) # Note that params_pm in Psychometric_fit has only 2 fit parameters...
    for i_tdur in range(len(t_dur_list_duration)):
        t_dur_temp = t_dur_list_duration[i_tdur]
        for i_OUpos in range(len(OU_pos_range)):
            res_temp = minimize(Psychometric_fit_D, param_fit_0_duration, args = ([Prob_final_corr_duration_scan_OUpos[i_tdur,:,i_OUpos]]))     #Note that mu_0_list is intrinsically defined in the Psychometric_fit function
            psychometric_params_list_duration_scan_OUpos[:,i_tdur,i_OUpos] = res_temp.x
        for i_OUneg in range(len(OU_neg_range)):
            res_temp = minimize(Psychometric_fit_D, param_fit_0_duration, args = ([Prob_final_corr_duration_scan_OUneg[i_tdur,:,i_OUneg]]))     #Note that mu_0_list is intrinsically defined in the Psychometric_fit function
            psychometric_params_list_duration_scan_OUneg[:,i_tdur,i_OUneg] = res_temp.x


    ## Fit Psychometric Threshold with a decaying exponential + Constant
    # Note that we would want to change varaibles_list at the top, to do a scan of OU-parameters
    param_fit_threshold_duration = [15., 0.2, 0., 100.] # Temp, initial guess for param_pm for Psychometric_fit_D.
    n_skip_fit_list_OUpos = np.zeros(len(OU_pos_range)).astype(int) # n_skips should only be integers
    n_skip_fit_list_OUneg = np.zeros(len(OU_neg_range)).astype(int)
    threshold_fit_params_list_duration_scan_OUpos = np.zeros((len(param_fit_threshold_duration), len(OU_pos_range))) # Note that params_pm in Psychometric_fit has only 2 fit parameters...
    threshold_fit_params_list_duration_scan_OUneg = np.zeros((len(param_fit_threshold_duration), len(OU_neg_range))) # Note that params_pm in Psychometric_fit has only 2 fit parameters...
    for i_OUpos in range(len(OU_pos_range)):
        n_skip_fit_OUpos = int(np.sum( psychometric_params_list_duration_scan_OUpos[0,:,i_OUpos]*100./mu_0  > coh_skip_threshold)) # First define which how many terms in the pscyhomeric_params_list to skip/ not include in fit. All data that has threshold >100% is removed.
        n_skip_fit_list_OUpos[i_OUpos] = n_skip_fit_OUpos
        res_scan_OUpos = minimize(Threshold_D_fit, param_fit_threshold_duration, args = (psychometric_params_list_duration_scan_OUpos[0,:,i_OUpos]*100./mu_0, n_skip_fit_OUpos, t_dur_list_duration))     #Note that mu_0_list is intrinsically defined in the Psychometric_fit function
        threshold_fit_params_list_duration_scan_OUpos[:,i_OUpos] = res_scan_OUpos.x
    for i_OUneg in range(len(OU_neg_range)):
        n_skip_fit_OUneg = int(np.sum( psychometric_params_list_duration_scan_OUneg[0,:,i_OUneg]*100./mu_0  > coh_skip_threshold)) # First define which how many terms in the pscyhomeric_params_list to skip/ not include in fit. All data that has threshold >100% is removed.
        n_skip_fit_list_OUneg[i_OUneg] = n_skip_fit_OUneg
        res_scan_OUneg = minimize(Threshold_D_fit, param_fit_threshold_duration, args = (psychometric_params_list_duration_scan_OUneg[0,:,i_OUneg]*100./mu_0, n_skip_fit_OUneg, t_dur_list_duration))     #Note that mu_0_list is intrinsically defined in the Psychometric_fit function
        threshold_fit_params_list_duration_scan_OUneg[:,i_OUneg] = res_scan_OUneg.x


    figD_params = plt.figure(figsize=(8,10.5))
    axD_params1 = figD_params.add_subplot(211)
    for i_OUpos in range(len(OU_pos_range)):
        axD_params1.plot(threshold_fit_params_list_duration_scan_OUpos[1, i_OUpos], threshold_fit_params_list_duration_scan_OUpos[0, i_OUpos], color=color_list[3], marker="x")         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    for i_OUneg in range(len(OU_neg_range)):
        axD_params1.plot(threshold_fit_params_list_duration_scan_OUneg[1, i_OUneg], threshold_fit_params_list_duration_scan_OUneg[0, i_OUneg], color=color_list[4], marker="x")         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    ## Also plot the 3 standard cases for illustration
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axD_params1.plot(threshold_fit_params_list_duration[1, i_models], threshold_fit_params_list_duration[0, i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use], marker="o")         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    #    axD_params1.axhline(Prob_final_corr_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # axD_params1.set_ylim([10.,100.])
    axD_params1.set_xlabel('Decay Time Constant (s)')
    axD_params1.set_ylabel('Threshold Asymptote (%)')
    axD_params1.set_title('Psychometric function Decision Threshold')
    # axD_params1.set_yscale('log')
    axD_params1.legend(loc=2)

    axD_params2 = figD_params.add_subplot(212)
    for i_OUpos in range(len(OU_pos_range)):
        axD_params2.plot(t_dur_list_duration, psychometric_params_list_duration_scan_OUpos[0,:,i_OUpos]*100./mu_0, color=color_list[4] )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
        axD_params2.plot(t_dur_list_duration, threshold_fit_params_list_duration_scan_OUpos[0, i_OUpos] + threshold_fit_params_list_duration_scan_OUpos[3, i_OUpos]*(np.exp(-((t_dur_list_duration-threshold_fit_params_list_duration_scan_OUpos[2, i_OUpos])/threshold_fit_params_list_duration_scan_OUpos[1, i_OUpos]))), color=color_list[3], linestyle="--" )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    for i_OUneg in range(len(OU_neg_range)):
        axD_params2.plot(t_dur_list_duration, psychometric_params_list_duration_scan_OUneg[0,:,i_OUneg]*100./mu_0, color=color_list[4] )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
        axD_params2.plot(t_dur_list_duration, threshold_fit_params_list_duration_scan_OUneg[0, i_OUneg] + threshold_fit_params_list_duration_scan_OUneg[3, i_OUneg]*(np.exp(-((t_dur_list_duration-threshold_fit_params_list_duration_scan_OUneg[2, i_OUneg])/threshold_fit_params_list_duration_scan_OUneg[1, i_OUneg]))), color=color_list[4], linestyle="--" )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    ## Also plot the 3 standard cases for illustration
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axD_params2.plot(t_dur_list_duration, psychometric_params_list_duration[0,:,i_models]*100./mu_0, color=color_list[index_model_2use], label=labels_list[index_model_2use] )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
        axD_params2.plot(t_dur_list_duration, threshold_fit_params_list_duration[0, i_models] + (threshold_fit_params_list_duration[3, i_models])*(np.exp(-((t_dur_list_duration-threshold_fit_params_list_duration[2, i_models])/threshold_fit_params_list_duration[1, i_models]))), color=color_list[index_model_2use], label=labels_list[index_model_2use], linestyle="--" )         # *100./mu_0 to convert the threshold from rel to mu_0 to coh level.
    # axD_params2.set_ylim([10.,100.])
    axD_params2.set_xlabel('Stimulation Duration (s)')
    axD_params2.set_ylabel('Threshold')
    axD_params2.set_title('Psychometric function Decision Threshold')
    # axD_params2.set_yscale('log')
    axD_params2.legend(loc=1)


    figD_params.savefig('Duration_paradigm_params_scan.pdf')
    np.save( "figS4_a_OUpos.npy", threshold_fit_params_list_duration_scan_OUpos)   #Resave everytime, just to make sure I don't mess anything up..
    np.save( "figS4_a_OUneg.npy", threshold_fit_params_list_duration_scan_OUneg)   #Resave everytime, just to make sure I don't mess anything up..
    np.save( "figS4_a_ref.npy"  , threshold_fit_params_list_duration)   #Resave everytime, just to make sure I don't mess anything up..
    np.save( "figS4_b_t_dur_list.npy", t_dur_list_duration)   #Resave everytime, just to make sure I don't mess anything up..
    np.save( "figS4_b_psychometric.npy", psychometric_params_list_duration[0,:,:]*100./mu_0)   #Resave everytime, just to make sure I don't mess anything up..
    # np.save( "figS4_b_psychometric_fitted.npy", threshold_fit_params_list_duration[0, :] + (threshold_fit_params_list_duration[3, :])*(np.exp(-((t_dur_list_duration-threshold_fit_params_list_duration[2, :])/threshold_fit_params_list_duration[1, :]))))   #Resave everytime, just to make sure I don't mess anything up..




#
#
#
# ########################################################################################################################
# Psychophysical Kerenel (PK)...

if Flag_PK:
    ## Initialization
    n_rep_PK = 1000          # Number of PK runs
    models_list = [0,3,4] #List of models to use. See Setting_list
    # models_list = models_list_all #List of models to use. See Setting_list
    mu_0_PK      = mu_0
    coh_list_PK  = np.array([-25.6, -12.8, -6.4, 6.4, 12.8, 25.6])
    mu_0_list_PK = [mu_0_PK*0.01*coh_temp_PK for coh_temp_PK in coh_list_PK]
    dt_mu_PK = 0.05         #[s] Duration of step for each mu in PK
    # mu_t_list_PK = np.zeros(int(T_dur/dt_mu_PK), n_rep_PK, len(models_list))

    # Prob_final_corr_PK  = np.zeros((n_rep_PK, len(mu_0_list_PK), len(models_list)))
    # Prob_final_err_PK   = np.zeros((n_rep_PK, len(mu_0_list_PK), len(models_list)))
    # Prob_final_undec_PK = np.zeros((n_rep_PK, len(mu_0_list_PK), len(models_list)))
    # Mean_Dec_Time_PK    = np.zeros((n_rep_PK, len(mu_0_list_PK), len(models_list)))

    PK_Amp       = np.zeros((int(T_dur/dt_mu_PK), len(mu_0_list_PK), len(models_list)))
    PK_n_trials  = np.zeros((int(T_dur/dt_mu_PK), len(mu_0_list_PK), len(models_list))) # Number of trials run in that slot of the matrix. Used for normalization when doing averaging.


    ## Run the trials
    ## For each models, find the probability to be correct/erred/undec for various mu and t_onset_pulse
    t_list_temp = t_list # If cutoff time is constant/ indep of T_dur
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        for i_rep_PK in range(n_rep_PK): # For now use the same mu_t for all models and mu, can fix later...
            print i_rep_PK
            ind_mu_t_list_PK_temp = np.random.randint(len(mu_0_list_PK), size=int(T_dur/dt_mu_PK))
            mu_t_list_PK_temp = np.zeros((int(T_dur/dt_mu_PK)))
            for i_mu_t_PK in range(len(mu_t_list_PK_temp)):
                mu_t_list_PK_temp[i_mu_t_PK] = mu_0_list_PK[ind_mu_t_list_PK_temp[i_mu_t_PK]]
            # mu_t_list_PK[:, i_rep_PK, i_models] = mu_t_list_PK_temp        #Record the states
            (Prob_list_corr_PK_temp, Prob_list_err_PK_temp) = DDM_pdf_general([0., param_mu_x_list[index_model_2use], param_mu_t_list[index_model_2use], sigma_0, param_sigma_x_list[index_model_2use], param_sigma_t_list[index_model_2use], B, param_B_t_list[index_model_2use], mu_t_list_PK_temp], index_model_2use, 1)                               # Simple DDM
            Prob_list_sum_corr_PK_temp = np.sum(Prob_list_corr_PK_temp) # No need cumsum, just sum.
            Prob_list_sum_err_PK_temp  = np.sum(Prob_list_err_PK_temp)
            # Prob_list_sum_undec_PK_temp  = 1. - Prob_list_sum_corr_PK_temp - Prob_list_sum_err_PK_temp # No need for undecided results, as we only want corr - err, while the undecided trials are spread evenly between the 2.
            PK_Amp_temp = Prob_list_sum_corr_PK_temp - Prob_list_sum_err_PK_temp
            for i_t_PK in range(int(T_dur/dt_mu_PK)):
                PK_Amp[i_t_PK, ind_mu_t_list_PK_temp[i_t_PK], i_models] += Prob_list_sum_corr_PK_temp - Prob_list_sum_err_PK_temp
                PK_n_trials[i_t_PK, ind_mu_t_list_PK_temp[i_t_PK], i_models] += 1

            #Outputs...
            # Prob_final_undec_PK[i_rep_PK, i_mu0, i_models] = Prob_list_cumsum_undec_PK_temp[-1]
            # Prob_final_corr_PK[ i_rep_PK, i_mu0, i_models] = Prob_list_cumsum_corr_PK_temp[-1] + Prob_final_undec_PK[i_rep_PK, i_mu0, i_models]/2.
            # Prob_final_err_PK[  i_rep_PK, i_mu0, i_models] = Prob_list_cumsum_err_PK_temp[-1]  + Prob_final_undec_PK[i_rep_PK, i_mu0, i_models]/2.
            # Mean_Dec_Time_PK[   i_rep_PK, i_mu0, i_models] = np.sum((Prob_list_cumsum_corr_PK_temp+Prob_list_cumsum_err_PK_temp) *t_list_temp) / np.sum((Prob_list_cumsum_corr_PK_temp+Prob_list_cumsum_err_PK_temp))

            ##Temp:
            # if index_model_2use ==1:
            #     Prob_final_corr_PK[i_tdur, i_models] = Prob_list_cumsum_corr_PK_temp[-1] / (Prob_list_cumsum_corr_PK_temp[-1] + Prob_list_cumsum_err_PK_temp[-1])
            #     Prob_final_err_PK[i_tdur, i_models]  = Prob_list_cumsum_err_PK_temp[-1] / (Prob_list_cumsum_corr_PK_temp[-1] + Prob_list_cumsum_err_PK_temp[-1])

    PK_Amp_runNorm = PK_Amp/PK_n_trials # Normalize the terms by the number of runs for each t_bin and mu level, for all models.
    PK_Amp_CohNorm = copy.copy(PK_Amp_runNorm) # PK_Amp_CohNorm is PK_Amp but divded by mu, for each of them.
    for i_coh_PK in range(len(coh_list_PK)):
        PK_Amp_CohNorm[:,i_coh_PK,:] /= coh_list_PK[i_coh_PK]
    PK_Amp_1D = np.mean(PK_Amp_CohNorm, axis=1)






    # Plots
    t_list_plot_PK = np.arange(0,T_dur, dt_mu_PK)
    figPK = plt.figure(figsize=(8,10.5))
    axPK1 = figPK.add_subplot(211)
    for i_models in range(len(models_list)):
        index_model_2use = models_list[i_models]
        axPK1.plot(t_list_plot_PK, PK_Amp_1D[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    #    axPK1.axhline(Prob_final_corr_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    #figPK.ylim([-1.,1.])
    axPK1.set_xlabel('mu_0 (~coherence)')
    axPK1.set_ylabel('PK Amp')
    axPK1.set_title('PsychoPhysical Amplitude, 1D')
#    axPK1.set_yscale('log')
    axPK1.legend(loc=1)

    plt.subplot(212)
    aspect_ratio = (t_list_plot_PK[-1]-t_list_plot_PK[0])/(mu_0_list_PK[-1]-mu_0_list_PK[0])
    plt.imshow(PK_Amp_CohNorm[:,:,0]           , extent=(mu_0_list_PK[0], mu_0_list_PK[-1], t_list_plot_PK[0], t_list_plot_PK[-1]), interpolation='nearest', cmap=matplotlib_cm.gist_rainbow, aspect=aspect_ratio)
    # set_xticklabels("g_KCa_d2") #Still have to figure out how to label axes
    plt.colorbar()
    #plt.xlabel(parameter_2_name +" (uA/cm2)")
    #plt.ylabel(parameter_1_name +" (uA/cm2)")
    plt.xlabel("t_bin (s)")
    plt.ylabel("mu_0 (~coherence)")
    plt.title('PsychoPhysical Amplitude, 2D, Control', fontsize=10)
    #plt.axis.set_xticklabels(labels, fontsize=8)


    # axPK3 = figPK.add_subplot(413)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axPK3.plot(t_dur_list_duration, Prob_final_undec_duration[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #    axPK3.axhline(Prob_final_undec_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # #figPK.ylim([-1.,1.])
    # #axPK3.set_xlabel('mu_0 (~coherence)')
    # axPK3.set_ylabel('Probability')
    # axPK3.set_title('Undecision Probability')
    # # axPK3.set_xscale('log')
    # axPK3.legend(loc=1)
    #
    # axPK4 = figPK.add_subplot(414)
    # for i_models in range(len(models_list)):
    #     index_model_2use = models_list[i_models]
    #     axPK4.plot(t_dur_list_duration, Mean_Dec_Time_duration[:,i_models], color=color_list[index_model_2use], label=labels_list[index_model_2use] )
    # #    axPK4.axhline(Mean_Dec_Time_0[index_model_2use], color=color_list[index_model_2use], linestyle="--")
    # #figPK.ylim([-1.,1.])
    # axPK4.set_xlabel('Duration (s)')
    # axPK4.set_ylabel('Time (s)')
    # axPK4.set_title('Mean Decision Time')
    # # axPK4.set_xscale('log')
    # axPK4.legend(loc=3)

    figPK.savefig('Psychophysical_Kernel.pdf')






    np.save("PK_Amp_2D_noNorm_10kruns_7.npy", PK_Amp)   #Resave everytime, just to make sure I don't mess anything up..
    np.save("PK_n_runs_2D_10kruns_7.npy"    , PK_n_trials)   #Resave everytime, just to make sure I don't mess anything up..