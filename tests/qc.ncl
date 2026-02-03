begin
;Set the file names here.  
;The outpput files from SOCA are netcdf 4.  The setfiloption is required to read
;these files in NCL.
  setfileoption("nc", "FileStructure", "Advanced") ; Required for Group access in NCL
  ;f = addfile("wod_t_ctd.nc", "r")
  ;f = addfile("sst_avhrr_mb_l3u.nc", "r")  
  f = addfile("icec_amsr2_north.nc", "r")

;No changes need to be made here. f=> is the NCL symbol for reading netcdf4 groups.
  g_obs  = f=>ObsValue
  g_oman = f=>oman
  g_ombg = f=>ombg
  g_meta = f=>MetaData 
  g_qc   = f=>EffectiveQC0

;-----------------------------------------
;Change the variable to the one in the input files.
;Just uncomment the variable that you want.
 ;Values for wod files.
 ; obs_val  = g_obs->waterTemperature
 ; oman_val = g_oman->waterTemperature
 ; ombg_val = g_ombg->waterTemperature
 ; qc_vals  = g_qc->waterTemperaute
 

 ;Values for sst files
 ; obs_val  = g_obs->seaSurfaceTemperature
 ; oman_val = g_oman->seaSurfaceTemperature
 ; ombg_val = g_ombg->seaSurfaceTemperature
 ; qc_vals  = g_qc->seaSurfaceTemperature
 
 ;Values for the icec files
 obs_val  = g_obs->seaIceFraction
 oman_val = g_oman->seaIceFraction
 ombg_val = g_ombg->seaIceFraction
 qc_vals  = g_qc->seaIceFraction


;----------------------------------------
  lat      = g_meta->latitude
  lon      = g_meta->longitude

  ;No changes need to be made now.  
  obs_mean = avg(obs_val)           
  obs_std  = stddev(obs_val)       
  obs_med  = dim_median(obs_val)      
  obs_min  = min(obs_val)             
  obs_max  = max(obs_val)           

  oman_mean = avg(oman_val)           
  oman_std  = stddev(oman_val)       
  oman_med  = dim_median(oman_val)      
  oman_min  = min(oman_val)             
  oman_max  = max(oman_val)              


  ombg_mean = avg(ombg_val)             
  ombg_std  = stddev(ombg_val)         
  ombg_med  = dim_median(ombg_val)       
  ombg_min  = min(ombg_val)            
  ombg_max  = max(ombg_val)             

  print(obs_mean+" "+oman_mean+"  "+ombg_mean)
  print(obs_med+"  "+oman_med+"   "+ombg_med )
  print(obs_std+"  "+oman_std+"  "+ombg_std)
  print(obs_min+"  "+oman_min+"  "+ombg_min)
  print(obs_max+"  "+oman_max+"  "+ombg_max)

  print("------------------------------------")
;Now add the qc_threshold
  qc_threshold = 10.0
  mask_good = (qc_vals .le. qc_threshold) ; Keep flags 0-10, toss anything > 10
  obs_val  = where(mask_good,  obs_val,  obs_val@_FillValue)
  oman_val = where(mask_good,  oman_val, oman_val@_FillValue)
  ombg_val = where(mask_good,  ombg_val, ombg_val@_FillValue)

  obs_mean = avg(obs_val)           
  obs_std  = stddev(obs_val)       
  obs_med  = dim_median(obs_val)      
  obs_min  = min(obs_val)             
  obs_max  = max(obs_val)           

  oman_mean = avg(oman_val)           
  oman_std  = stddev(oman_val)       
  oman_med  = dim_median(oman_val)      
  oman_min  = min(oman_val)             
  oman_max  = max(oman_val)              


  ombg_mean = avg(ombg_val)             
  ombg_std  = stddev(ombg_val)         
  ombg_med  = dim_median(ombg_val)       
  ombg_min  = min(ombg_val)            
  ombg_max  = max(ombg_val)             

  print(obs_mean+" "+oman_mean+"  "+ombg_mean)
  print(obs_med+"  "+oman_med+"   "+ombg_med )
  print(obs_std+"  "+oman_std+"  "+ombg_std)
  print(obs_min+"  "+oman_min+"  "+ombg_min)
  print(obs_max+"  "+oman_max+"  "+ombg_max)


end
