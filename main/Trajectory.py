from math import *
import numpy as np
import numpy.linalg as alg

g = 9.81 # m^2/s
R_terre = 637000 # m

### Magicien d'Oz
# Vent
Vvent=np.mat('[7;175.]') # 175°, 7 kt

# Valeur par défaut, mis à jour dans computeTrajectory
lat_piste, long_piste, alti_piste, Cp, distance_finale, sens_tour_piste, largeur_piste, longueur_piste, hauteur_point_cible = (0,)*9

# Spécifications des terrains
# lat (deg), long (deg), alt (ft), cap (deg), dist finale (m), sens tdp, largeur (m), longueur (m), hauteur cible (ft)
# Sens tdp : 1 sens horaire, 0 sens trigo
airfieldSpecs = {
    "LFCL": (43.591060, 1.496512, 456, 155, 1000, 0, 22, 950, 1500),
    "LFBO": (43.619109, 1.371902, 499, 323, 1000, 0, 45, 3503, 1500),
    "LFBR": (43.447012, 1.269533, 623, 297, 1000, 0, 30, 1100, 1500)}

# lat_piste et long_piste servent de point de référence

# Conditions de vol au moment du déclenchement du déroutement
# Mises à jour par updateAircraftData
depart_deroutement=1
lat_avion_0=44 # en degré
long_avion_0=1.7
alti_avion_0=2500 # t
Avion_0=np.mat('[200;235;0]') # caractéristiques avion : V (km/h), Vz (ft/min), Cap (degré)
Xa0_p=(long_avion_0-long_piste)*2*pi/360*R_terre # coordonnées de l'avion dans le repère piste
Ya0_p=(lat_avion_0-lat_piste)*2*pi/360*R_terre
Za0_p=alti_avion_0/3.28084


### Fonctions
def rotation_vect(x,y,z,angle):
  Vect_r_1=np.zeros((3,1))
  Vect_r_1[0,0]=x
  Vect_r_1[1,0]=y
  Vect_r_1[2,0]=z
  Angle_rotation=angle
  Angle_rotation_rad=(Angle_rotation)*(2*pi)/360
  CDRR=np.zeros((3,3))
  CDRR[0,0]= cos(Angle_rotation_rad)
  CDRR[0,1]=-sin(Angle_rotation_rad)
  CDRR[1,0]= sin(Angle_rotation_rad)
  CDRR[1,1]= cos(Angle_rotation_rad)
  CDRR[2,2]=1
  return np.dot(CDRR,Vect_r_1)


def  translation_vect(x,y,z,Dx,Dy):
  Vect_tr_1 =np.zeros((3,1))
  Vect_tr_1[0,0]=x
  Vect_tr_1[1,0]=y
  Vect_tr_1[2,0]=z
  Vect_translation=np.zeros((3,1))
  Vect_translation[0,0]=Dx
  Vect_translation[1,0]=Dy
  return Vect_tr_1+Vect_translation


def correction_vent(Vsol_p,Ca_p,Vvent_kmh,Cv_p):
  Cv_p_rad=Cv_p*2*pi/360
  Ca_p_rad=Ca_p*2*pi/360
  Vxsol_p=Vsol_p*sin(Ca_p_rad)
  Vysol_p=Vsol_p*cos(Ca_p_rad)
  Vxvent_p=-Vvent_kmh*sin(Cv_p_rad)
  Vyvent_p=-Vvent_kmh*cos(Cv_p_rad)
  Vxvraie_p=Vxsol_p+Vxvent_p
  Vyvraie_p=Vysol_p+Vyvent_p
  if Ca_p>=270 : cste=2
  elif Ca_p<90 :cste=0
  elif Ca_p>=90 or Ca_p>=180:cste=1
  else: cste=0 ###DEBUG
  Ca_avecVent_p=np.arctan(Vxvraie_p/Vyvraie_p)*360/(2*pi)+cste*180
  corr_v=Ca_avecVent_p-Ca_p
  Ca_aSuivre_p=Ca_p-corr_v
  if Ca_aSuivre_p>360:  Ca_aSuivre_p=Ca_aSuivre_p-360
  return Ca_aSuivre_p


def x_2_long(x,longRef):
  long_x=x*360/(R_terre*2*pi)+longRef
  return long_x


def y_2_lat(y,latRef):
  long_y=y*360/(R_terre*2*pi)+latRef
  return long_y


def updateAircraftData(db):
  """
  Update aircraft data from database
  """
  global lat_avion_0, long_avion_0, alti_avion_0, Avion_0, Xa0_p, Ya0_p, Za0_p
  lat_avion_0 = db.getFlightParam("latitude_deg") # en degré
  long_avion_0 = db.getFlightParam("longitude_deg")
  alti_avion_0 = db.getFlightParam("altitude_ft") # ft
  Avion_0 = np.mat('['+
    str(db.getFlightParam("airspeed_kt")/1.852)+ # km/h
    ';'+
    str(db.getFlightParam("vspeed_fps")*60)+ # ft/min
    ';'+
    str(db.getFlightParam("heading_deg"))+
    ']')
  Xa0_p=(long_avion_0-long_piste)*2*pi/360*R_terre # coordonnées de l'avion dans le repère piste
  Ya0_p=(lat_avion_0-lat_piste)*2*pi/360*R_terre
  Za0_p=alti_avion_0/3.28084


def convertToMarkers(points):
  """
  Converts Avion list to GOOGLE MAPS JS markers (JSON)
  N.B. AVION matrice 6x12 des positions où passer pour le déroutement
  0 -> longitude
  1 -> latitude
  2 -> altitude
  5 -> cap (heading)
  """
  list_markers = []
  for i,pos in enumerate(points):
    marker = dict()
    marker = {"id": "air_gate_%d" % (i+1), "content": "<h3>Air gate %d</h3>" % (i+1), "coords": {"lat": pos[1], "lng": pos[0]}, "alt": pos[2], "heading": pos[5]}
    list_markers.append(marker)

  # stringified_array_markers = json.dumps(your_data, ensure_ascii=False)
  return list_markers

def nonNan(points):
  """
  Filters out "nan" points
  """
  res = []
  for i in range(len(points)):
    if np.isnan(points[i,0]):
      break
    for j in range(len(points[i,:])):
      if np.isnan(points[i,j]):
        points[i,j] = -1
    res.append(points[i,:])
  return convertToMarkers(res)


def computeTrajectory(db, airfield):
  """
  Main function, returns checkpoints
  """
  global lat_avion_0, long_avion_0, alti_avion_0, Avion_0, Xa0_p, Ya0_p, Za0_p

  # Mise à jour du terrain
  lat_piste, long_piste, alti_piste, Cp, distance_finale, sens_tour_piste, largeur_piste, longueur_piste, hauteur_point_cible = airfieldSpecs[airfield]

  updateAircraftData(db)

  # Vvent dans le repère pisteSeuil
  Vvent_kmh=Vvent[0,0]*1.852 # km/h
  Angle_vent=Vvent[1,0] # degré

  # Caractéristiques de la zone entourant la piste de destination
  Zpc_ps=hauteur_point_cible/3.28#m
  Xlimd=largeur_piste/2+1000
  Xlimg=-Xlimd
  Ylimh=longueur_piste+distance_finale
  Ylimb=-distance_finale
  Zlimh=2*Zpc_ps
  Zlimb=0
  Zpc_ps=hauteur_point_cible/3.28#m

  # Coordonnées du point cible par rapport au repère pisteSeuil
  Pos_cible=np.zeros((3,1))
  Pos_cible[1,0]=longueur_piste+distance_finale
  Pos_cible[2,0]=hauteur_point_cible

  # Cap avion
  Ca_p=Avion_0[2]
  Ca_ps=Ca_p-Cp

  # Vitesse sol au début du déroutement m/s
  Va=Avion_0[0,0]/3.6

  # Initialisation des valeurs
  Ca0_p, Ca1_p, Ca2_p, Ca3_p, Ca4_p, Ca5_p, Ca6_p, Ca7_p, Ca8_p, Ca9_p, Ca10_p, Ca11_p, Ca12_p = (None,)*13

  t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11, t12 = (None,)*12
  t21_t1, t2_t1, t3_t2, t4_t3, t5_t4, t6_t5, t7_t6, t8_t7, t9_t8, t10_t9, t11_t10, t12_t11 = (None,)*12

  Xa1_p, Xa2_p, Xa3_p, Xa4_p, Xa5_p, Xa6_p, Xa7_p, Xa8_p, Xa9_p, Xa10_p, Xa11_p, Xa12_p = (None,)*12
  Ya1_p, Ya2_p, Ya3_p, Ya4_p, Ya5_p, Ya6_p, Ya7_p, Ya8_p, Ya9_p, Ya10_p, Ya11_p, Ya12_p = (None,)*12
  Za1_p, Za2_p, Za3_p, Za4_p, Za5_p, Za6_p, Za7_p, Za8_p, Za9_p, Za10_p, Za11_p, Za12_p = (None,)*12

  Xa1_ps, Xa2_ps, Xa3_ps, Xa4_ps, Xa5_ps, Xa6_ps, Xa7_ps, Xa8_ps, Xa9_ps, Xa10_ps, Xa11_ps, Xa12_ps = (None,)*12
  Ya1_ps, Ya2_ps, Ya3_ps, Ya4_ps, Ya5_ps, Ya6_ps, Ya7_ps, Ya8_ps, Ya9_ps, Ya10_ps, Ya11_ps, Ya12_ps = (None,)*12
  Za1_ps, Za2_ps, Za3_ps, Za4_ps, Za5_ps, Za6_ps, Za7_ps, Za8_ps, Za9_ps, Za10_ps, Za11_ps, Za12_ps = (None,)*12

  Avion=np.zeros((12,6))

  if depart_deroutement==1:
#-------------------------------position initiale de l'avion
    Ca0_p=Avion_0[1,0]
    Ca0_ps=Ca0_p-Cp
    Vect_1=rotation_vect(Xa0_p,Ya0_p,Za0_p,Cp)#coordonnées de l'avion de piste vers pisteSeuil
    Xa0_ps=Vect_1[0,0]
    Ya0_ps=Vect_1[1,0]
    Za0_ps=Za0_p
#-------------------------------point le plus proche de la position initiale de l'avion
    dist_A_Avion_0=sqrt((Xa0_ps-Xlimg)*(Xa0_ps-Xlimg)+(Ya0_ps-Ylimh)*(Ya0_ps-Ylimh))
    dist_min=dist_A_Avion_0
    pt=1
    Xpt_ps=Xlimg
    Ypt_ps=Ylimh

    dist_B_Avion_0=sqrt((Xa0_ps-Xlimd)*(Xa0_ps-Xlimd)+(Ya0_ps-Ylimh)*(Ya0_ps-Ylimh))
    if dist_B_Avion_0<dist_min :
       dist_min=dist_B_Avion_0
       pt=2
       Xpt_ps=Xlimd
       Ypt_ps=Ylimh
    #endIf

    dist_C_Avion_0=sqrt((Xa0_ps-Xlimd)*(Xa0_ps-Xlimd)+(Ya0_ps-Ylimb)*(Ya0_ps-Ylimb))
    if dist_C_Avion_0<dist_min :
       dist_min=dist_C_Avion_0
       pt=3
       Xpt_ps=Xlimd
       Ypt_ps=Ylimb
    #endIf

    dist_D_Avion_0=sqrt((Xa0_ps-Xlimg)*(Xa0_ps-Xlimg)+(Ya0_ps-Ylimb)*(Ya0_ps-Ylimb))
    if dist_D_Avion_0<dist_min :
       dist_min=dist_D_Avion_0
       pt=4
       Xpt_ps=Xlimg
       Ypt_ps=Ylimb
    #endIf
#-----------------------------------------------------------branche la plus adaptée
    br = 1 ###DEBUG
    #cas2
    if sens_tour_piste==0 and pt==3: br=2 #br: branche
    elif sens_tour_piste==1 and pt==3: br=1
    #cas4
    if sens_tour_piste==0 and pt==2: br=3
    elif sens_tour_piste==1 and pt==2: br=2
    #cas6
    if sens_tour_piste==0 and pt==1: br=4
    elif sens_tour_piste==1 and pt==1: br=3
    #cas8
    if sens_tour_piste==0 and pt==4: br=1
    elif sens_tour_piste==1 and pt==4: br=4
    #endIf
#-------------------------------------------------------------premier virage
    sens_virage1=-1#-1 virage gauche, 1 si virage droite 
    teta_c=0#degré
    teta_c_rad=teta_c*2*pi/360#rad
    inclinaison=30#degré
    inclinaison_rad=inclinaison*2*pi/360#rad
    R1=Va*Va/(g*tan(inclinaison_rad))#m
#-------------------coordonnées du centre du cercle repère avion vers repère pisteSeuil
    Xr_a=sens_virage1*R1
    Yr_a=0
    Zr_a=0
    Vect_4=rotation_vect(Xr_a,Yr_a,Zr_a,-Ca0_ps)+translation_vect(0,0,0,Xa0_ps,Ya0_ps)
    Xr_ps=Vect_4[0,0]
    Yr_ps=Vect_4[1,0]
    Zr_ps=Vect_4[2,0]

#-------------------calcul de la distance entre le point visé et le centre du cercle
    X_ps=Xa0_ps
    Y_ps=Ya0_ps
    d1=sqrt((X_ps-Xpt_ps)*(X_ps-Xpt_ps)+(Y_ps-Ypt_ps)*(Y_ps-Ypt_ps));  
#-------------------calcul de la distance entre le point visé et le centre du cercle
    d2=sqrt((Xr_ps-Xpt_ps)*(Xr_ps-Xpt_ps)+(Yr_ps-Ypt_ps)*(Yr_ps-Ypt_ps)-R1*R1)
#-------------------calcul de la distance entre le point visé et l'avion
    d3=sqrt((Xa0_ps-Xpt_ps)*(Xa0_ps-Xpt_ps)+(Ya0_ps-Ypt_ps)*(Ya0_ps-Ypt_ps))
#------------------------------------point évoluant sur le cercle de rayon R1 dans le repère cercle
#----------------boucle sur teta_c pour que d1=d2 
    iter1=0
    iter2=0
    while d1<d2 and iter1<100:
      X_c=R1*cos(teta_c_rad)
      Y_c=R1*sin(teta_c_rad)
      Z_c=Za0_p
#--------------------point évoluant sur le cercle de rayon R1 dans le repère avion: translation de (sens_virage*R1,0)
      Vect_2=translation_vect(X_c,Y_c,Z_c,sens_virage1*R1,0)
      X_a=Vect_2[0,0]
      Y_a=Vect_2[1,0]
      Z_a=Vect_2[2,0]
#--------------point évoluant sur le cercle de rayon R1 dans le repère pisteSeuil: rotation d'angle -Ca0_ps 
#--------------et translation de (Xa0_ps,Ya0_ps)
      Vect_3=rotation_vect(X_a,Y_a,Z_a,-Ca0_ps)+translation_vect(0,0,0,Xa0_ps,Ya0_ps)
      X_ps=Vect_3[0,0]
      Y_ps=Vect_3[1,0]
      Z_ps=Vect_3[2,0]
#--------------calcul de d1
      d1=sqrt((X_ps-Xpt_ps)*(X_ps-Xpt_ps)+(Y_ps-Ypt_ps)*(Y_ps-Ypt_ps))
      teta_c_rad=teta_c_rad-sens_virage1*0.1
      iter1=iter1+1
    #end If
    while d1>=d2 and iter2<100:
      X_c=R1*cos(teta_c_rad)
      Y_c=R1*sin(teta_c_rad)
      Z_c=Za0_p
#--------------------point évoluant sur le cercle de rayon R1 dans le repère avion: translation de (sens_virage*R1,0)
      Vect_21=translation_vect(X_c,Y_c,Z_c,sens_virage1*R1,0)
      X_a=Vect_21[0,0]
      Y_a=Vect_21[1,0]
      Z_a=Vect_21[2,0]
#--------------point évoluant sur le cercle de rayon R1 dans le repère pisteSeuil: rotation d'angle -Ca0_ps 
#--------------et translation de (Xa0_ps,Ya0_ps)
      Vect_31=rotation_vect(X_a,Y_a,Z_a,-Ca0_ps)+translation_vect(0,0,0,Xa0_ps,Ya0_ps)
      X_ps=Vect_31[0,0]
      Y_ps=Vect_31[1,0]
      Z_ps=Vect_31[2,0]
#--------------calcul de d1
      d1=sqrt((X_ps-Xpt_ps)*(X_ps-Xpt_ps)+(Y_ps-Ypt_ps)*(Y_ps-Ypt_ps))
      teta_c_rad=teta_c_rad-sens_virage1*0.1
      iter2=iter2+1
    #end While
    teta_c=teta_c_rad*360/(2*pi)
#-------------calcul du temps de virage
    tps_virage1=teta_c_rad/(g*tan(inclinaison_rad)/Va)
    t1=tps_virage1
    
#----------------------------L'avion se trouve en sortie de cercle/ligne droite à 150km/h (point n°1)
    Xa1_ps=X_ps
    Ya1_ps=Y_ps
    Za1_ps=Z_ps
    if Xa1_ps<Xlimg and Ya1_ps<Ylimb:
      cste1=0
    elif Xa1_ps>Xlimd and Ya1_ps<Ylimb:
      cste1=360
    elif Xa1_ps>Xlimd and Ya1_ps>Ylimh:
      cste1=180;  
    elif Xa1_ps<Xlimg and Ya1_ps>Ylimh:
      cste1=180
    else:
      cste1=0 ###DEBUG
    #end If
#--------------------------------Cap après virage 1
    Ca1_ps=cste1+np.arctan((Xa1_ps-Xpt_ps)/(Ya1_ps-Ypt_ps))*360/(2*pi)
    Ca1_p=Ca1_ps+Cp
    Ca1_p=correction_vent(Va,Ca1_p,Vvent_kmh,Angle_vent)
#--------------Vitesse avion sur le segment 1-2 = Va 
#---------temps de parcours entre t1 et t21
    t21_t1=sqrt((Xa1_ps-Xpt_ps)*(Xa1_ps-Xpt_ps)+(Ya1_ps-Ypt_ps)*(Ya1_ps-Ypt_ps))/Va

#---------Calcul du temps t2
    delta_teta=0
    
    if Xa1_ps<Xlimg and Ya1_ps<Ylimb and sens_tour_piste==0:
      delta_teta=90-Ca1_ps
      sens_virage2=1
    elif Xa1_ps<Xlimg and Ya1_ps<Ylimb and sens_tour_piste==1:
      delta_teta=0-Ca1_ps
      sens_virage2=-1

    elif Xa1_ps>Xlimd and Ya1_ps<Ylimb and sens_tour_piste==0:
      delta_teta=0-Ca1_ps
      sens_virage2=1
    elif Xa1_ps>Xlimd and Ya1_ps<Ylimb and sens_tour_piste==1:
      delta_teta=270-Ca1_ps
      sens_virage2=-1

    elif Xa1_ps>Xlimd and Ya1_ps>Ylimh and sens_tour_piste==0:
      delta_teta=270-Ca1_ps
      sens_virage2=1
    elif Xa1_ps>Xlimd and Ya1_ps>Ylimh and sens_tour_piste==1:
      delta_teta=180-Ca1_ps
      sens_virage2=-1

    elif Xa1_ps<Xlimg and Ya1_ps>Ylimh and sens_tour_piste==0:
      delta_teta=180-Ca1_ps
      sens_virage2=1
    elif Xa1_ps<Xlimg and Ya1_ps>Ylimh and sens_tour_piste==1:
      delta_teta=90-Ca1_ps
      sens_virage2=-1

    #---------------------------------distance entre t2 et t21, à partir de t2 on vole à 150 km/h
    V=150/3.6#vitesse sol m/s
    R2=V*V/(g*tan(inclinaison_rad))
    w2=g*tan(inclinaison_rad)/V
    delta_teta_rad=delta_teta*2*pi/360
    
    #--------------calcul de t2-t0
    t2=t21_t1+tps_virage1
    #--------------calcul de t2-t1
    t2_t1=t21_t1
    
#----------------coordonnées du point 2 (point n°2)
    Xa2_ps=Xpt_ps
    Ya2_ps=Ypt_ps
    Za2_ps=Zpc_ps#descente pendant la première ligne droite
#-------------------------------------------------------deuxième virage
    #-------------------------Cap avion après virage 2
    Ca2_ps=delta_teta+Ca1_ps
    Ca2_p=Ca2_ps+Cp
    Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)

#-------------------------------------ligne droite 2
    #------------coordonnées du point en fin de la ligne droite (point n°4)
    
#-----------------------------------------------------------------------------intégration branche 1/Tdp gauche
    if br==1 and sens_tour_piste==0:
      Xa4_ps=0
      Ya4_ps=Ylimb
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t3
      t4_t2=sqrt((Xa4_ps-Xa2_ps)*(Xa4_ps-Xa2_ps))/V
    #------------temps t4
      t4=t4_t2+t2
    #------------descente du point n°4 au seuil de la piste (point n°5)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa5_ps=0
      Ya5_ps=0
      Za5_ps=0
      Vaz5=2.54
      Ca4_ps=0
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t5
      t5_t4=(Za4_ps-Za5_ps)/Vaz5
      t5=t5_t4+t4
      Ca5_p=Cp
      
#-----------------------------------------------------------------------------intégration branche 1/Tdp droite       
    if br==1 and sens_tour_piste==1:
      Xa4_ps=0
      Ya4_ps=Ylimb
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t2
      t4_t2=sqrt((Xa4_ps-Xa2_ps)*(Xa4_ps-Xa2_ps))/V
    #------------temps t4
      t4=t4_t2+t2
    #------------descente du point n°4 au seuil de la piste (point n°5)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa5_ps=0
      Ya5_ps=0
      Za5_ps=0
      Vaz5=2.54
      Ca4_ps=0
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t5
      t5_t4=(Za4_ps-Za5_ps)/Vaz5
      t5=t5_t4+t4
      Ca5_p=Cp
      
#-----------------------------------------------------------------------------intégration branche 2/Tdp droite
    if br==2 and sens_tour_piste==1:
      Xa4_ps=Xlimd
      Ya4_ps=Ylimb
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t3
      t4_t2=sqrt((Ya4_ps-Ya2_ps)*(Ya4_ps-Ya2_ps))/V
    #------------temps t4
      t4=t4_t2+t2
    #------------ligne droite entre point n°4 et point n°5
      Xa5_ps=0
      Ya5_ps=Ylimb
      Za5_ps=Zpc_ps
      t5_t4=sqrt((Xa5_ps-Xa4_ps)*(Xa5_ps-Xa4_ps))/V
      t5=t5_t4+t4
      Ca4_ps=270
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
    #------------descente du point n°5 au seuil de la piste (point n°6)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa6_ps=0
      Ya6_ps=0
      Za6_ps=0
      Vaz6=2.54
      Ca5_ps=0
      Ca5_p=Ca5_ps+Cp
      Ca5_p=correction_vent(V,Ca5_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t6
      t6_t5=(Za5_ps-Za6_ps)/Vaz6
      t6=t6_t5+t5;  
      Ca6_p=Cp
        
#-----------------------------------------------------------------------------intégration branche 2/Tdp gauche   
    if br==2 and sens_tour_piste==0:
      Xa4_ps=0
      Ya4_ps=Ylimb
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t2
      t4_t2=sqrt((Xa4_ps-Xa2_ps)*(Xa4_ps-Xa2_ps))/V
    #------------temps t4
      t4=t4_t2+t2;     
    #------------descente du point n°4 au seuil de la piste (point n°5)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa5_ps=0
      Ya5_ps=0
      Za5_ps=0
      Vaz5=2.54
      Ca4_ps=0
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t5
      t5_t4=(Za4_ps-Za5_ps)/Vaz5
      t5=t5_t4+t4;   
      Ca5_p=Cp
      
#-----------------------------------------------------------------------------intégration branche 3/Tdp droite
    if br==3 and sens_tour_piste==1:
      Xa4_ps=Xlimd
      Ya4_ps=Ylimh
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t2
      t4_t2=sqrt((Xa4_ps-Xa2_ps)*(Xa4_ps-Xa2_ps))/V
    #------------temps t4
      t4=t4_t2+t2
    #------------ligne droite entre point n°4 et point n°5
      Xa5_ps=Xlimd
      Ya5_ps=Ylimb
      Za5_ps=Zpc_ps
      t5_t4=sqrt((Ya5_ps-Ya4_ps)*(Ya5_ps-Ya4_ps))/V
      t5=t5_t4+t4
      Ca4_ps=180
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
    #------------ligne droite entre point n°5 et point n°6
      Xa6_ps=0
      Ya6_ps=Ylimb
      Za6_ps=Zpc_ps
      t6_t5=sqrt((Xa6_ps-Xa5_ps)*(Xa6_ps-Xa5_ps))/V
      t6=t6_t5+t5
      Ca5_ps=270
      Ca5_p=Ca5_ps+Cp
      Ca5_p=correction_vent(V,Ca5_p,Vvent_kmh,Angle_vent);     
    #------------descente du point n°6 au seuil de la piste (point n°7)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa7_ps=0
      Ya7_ps=0
      Za7_ps=0
      Vaz7=2.54
      Ca6_ps=0
      Ca6_p=Ca6_ps+Cp
      Ca6_p=correction_vent(V,Ca6_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t7
      t7_t6=(Za6_ps-Za7_ps)/Vaz7
      t7=t7_t6+t6;     
      Ca7_p=Cp
      
#-----------------------------------------------------------------------------intégration branche 3/Tdp gauche    
    if br==3 and sens_tour_piste==0:
      Xa4_ps=Xlimg
      Ya4_ps=Ylimh
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t2
      t4_t2=sqrt((Xa4_ps-Xa2_ps)*(Xa4_ps-Xa2_ps))/V
    #------------temps t4
      t4=t4_t2+t2
    #------------ligne droite entre point n°4 et point n°5
      Xa5_ps=Xlimg
      Ya5_ps=Ylimb
      Za5_ps=Zpc_ps
      t5_t4=sqrt((Ya5_ps-Ya4_ps)*(Ya5_ps-Ya4_ps))/V
      t5=t5_t4+t4
      Ca4_ps=180
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
    #------------ligne droite entre point n°5 et point n°6
      Xa6_ps=0
      Ya6_ps=Ylimb
      Za6_ps=Zpc_ps
      t6_t5=sqrt((Xa6_ps-Xa5_ps)*(Xa6_ps-Xa5_ps))/V
      t6=t6_t5+t5
      Ca5_ps=90
      Ca5_p=Ca5_ps+Cp
      Ca5_p=correction_vent(V,Ca5_p,Vvent_kmh,Angle_vent);     
    #------------descente du point n°6 au seuil de la piste (point n°7)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa7_ps=0
      Ya7_ps=0
      Za7_ps=0
      Vaz7=2.54
      Ca6_ps=0
      Ca6_p=Ca6_ps+Cp
      Ca6_p=correction_vent(V,Ca6_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t7
      t7_t6=(Za6_ps-Za7_ps)/Vaz7
      t7=t7_t6+t6
      Ca7_p=Cp
    
#-----------------------------------------------------------------------------intégration branche 4/Tdp droite
    if br==4 and sens_tour_piste==1:
      Xa4_ps=Xlimg
      Ya4_ps=Ylimh
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t2
      t4_t2=sqrt((Ya4_ps-Ya2_ps)*(Ya4_ps-Ya2_ps))/V
    #------------temps t4
      t4=t4_t2+t2
    #------------ligne droite entre point n°4 et point n°5
      Xa5_ps=Xlimd
      Ya5_ps=Ylimh
      Za5_ps=Zpc_ps
      t5_t4=sqrt((Xa5_ps-Xa4_ps)*(Xa5_ps-Xa4_ps))/V
      t5=t5_t4+t4
      Ca4_ps=90
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
    #------------ligne droite entre point n°5 et point n°6
      Xa6_ps=Xlimd
      Ya6_ps=Ylimb
      Za6_ps=Zpc_ps
      t6_t5=sqrt((Ya5_ps-Ya6_ps)*(Ya5_ps-Ya6_ps))/V
      t6=t6_t5+t5
      Ca5_ps=180
      Ca5_p=Ca5_ps+Cp
      Ca5_p=correction_vent(V,Ca5_p,Vvent_kmh,Angle_vent);     
    #------------ligne droite entre point n°6 et point n°7
      Xa7_ps=0
      Ya7_ps=Ylimb
      Za7_ps=Zpc_ps
      t7_t6=sqrt((Xa6_ps-Xa7_ps)*(Xa6_ps-Xa7_ps))/V
      t7=t7_t6+t6
      Ca6_ps=270
      Ca6_p=Ca6_ps+Cp
      Ca6_p=correction_vent(V,Ca6_p,Vvent_kmh,Angle_vent);   
    #------------descente du point n°7 au seuil de la piste (point n°8)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa8_ps=0
      Ya8_ps=0
      Za8_ps=0
      Vaz8=2.54
      Ca7_ps=0
      Ca7_p=Ca7_ps+Cp
      Ca7_p=correction_vent(V,Ca7_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t8
      t8_t7=(Za7_ps-Za8_ps)/Vaz8
      t8=t8_t7+t7;  
      Ca8_p=Cp
#-----------------------------------------------------------------------------intégration branche 4/Tdp gauche
    if br==4 and sens_tour_piste==0:
      Xa4_ps=Xlimg
      Ya4_ps=Ylimb
      Za4_ps=Zpc_ps
      Ca2_p=correction_vent(V,Ca2_p,Vvent_kmh,Angle_vent)
    #------------temps entre t4 et t2
      t4_t2=sqrt((Ya4_ps-Ya2_ps)*(Ya4_ps-Ya2_ps))/V
    #------------temps t4
      t4=t4_t2+t2
    #------------ligne droite entre point n°4 et point n°5
      Xa5_ps=0
      Ya5_ps=Ylimb
      Za5_ps=Zpc_ps
      t5_t4=sqrt((Xa5_ps-Xa4_ps)*(Xa5_ps-Xa4_ps))/V
      t5=t5_t4+t4
      Ca4_ps=90
      Ca4_p=Ca4_ps+Cp
      Ca4_p=correction_vent(V,Ca4_p,Vvent_kmh,Angle_vent)
   #------------descente du point n°5 au seuil de la piste (point n°6)
    #-500ft/min=>2.54m/s, V=140km/h
      Xa6_ps=0
      Ya6_ps=0
      Za6_ps=0
      Vaz6=2.54
      Ca5_ps=0
      Ca5_p=Ca5_ps+Cp
      Ca5_p=correction_vent(V,Ca5_p,Vvent_kmh,Angle_vent)
    #---------calcul du temps où l'on atterrit t6
      t6_t5=(Za5_ps-Za6_ps)/Vaz6
      t6=t6_t5+t5
      Ca6_p=Cp
      
#----------------transfert dans le référentiel piste
    Avion[0,0]=long_avion_0
    Avion[0,1]=lat_avion_0
    Avion[0,2]=Za0_p
    Avion[0,3]=0
    Avion[0,4]=0
    Avion[0,5]=Ca0_p

    Vect_1ps=rotation_vect(Xa1_ps,Ya1_ps,Za1_ps,-Cp)
    Avion[1,0]=x_2_long(Vect_1ps[0,0],long_piste)
    Avion[1,1]=y_2_lat(Vect_1ps[1,0],lat_piste)
    Avion[1,2]=Vect_1ps[2,0]
    Avion[1,3]=t1
    Avion[1,4]=t1
    Avion[1,5]=Ca1_p
    
    Vect_2ps=rotation_vect(Xa2_ps,Ya2_ps,Za2_ps,-Cp)
    Avion[2,0]=x_2_long(Vect_2ps[0,0],long_piste)
    Avion[2,1]=y_2_lat(Vect_2ps[1,0],lat_piste)
    Avion[2,2]=Vect_2ps[2,0]
    Avion[2,3]=t2_t1
    Avion[2,4]=t2
    Avion[2,5]=Ca2_p
    
    Vect_4ps=rotation_vect(Xa4_ps,Ya4_ps,Za4_ps,-Cp)
    Avion[3,0]=x_2_long(Vect_4ps[0,0],long_piste)
    Avion[3,1]=y_2_lat(Vect_4ps[1,0],lat_piste)
    Avion[3,2]=Vect_4ps[2,0]
    Avion[3,3]=t4_t2
    Avion[3,4]=t4
    Avion[3,5]=Ca4_p

    Vect_5ps=rotation_vect(Xa5_ps,Ya5_ps,Za5_ps,-Cp)
    Avion[4,0]=x_2_long(Vect_5ps[0,0],long_piste)
    Avion[4,1]=y_2_lat(Vect_5ps[1,0],lat_piste)
    Avion[4,2]=Vect_5ps[2,0]
    Avion[4,3]=t5_t4
    Avion[4,4]=t5
    Avion[4,5]=Ca5_p
    
    Vect_6ps=rotation_vect(Xa6_ps,Ya6_ps,Za6_ps,-Cp)
    Avion[5,0]=x_2_long(Vect_6ps[0,0],long_piste)
    Avion[5,1]=y_2_lat(Vect_6ps[1,0],lat_piste)
    Avion[5,2]=Vect_6ps[2,0]
    Avion[5,3]=t6_t5
    Avion[5,4]=t6
    Avion[5,5]=Ca6_p
    
    Vect_7ps=rotation_vect(Xa7_ps,Ya7_ps,Za7_ps,-Cp)
    Avion[6,0]=x_2_long(Vect_7ps[0,0],long_piste)
    Avion[6,1]=y_2_lat(Vect_7ps[1,0],lat_piste)
    Avion[6,2]=Vect_7ps[2,0]
    Avion[6,3]=t7_t6
    Avion[6,4]=t7
    Avion[6,5]=Ca7_p
    
    Vect_8ps=rotation_vect(Xa8_ps,Ya8_ps,Za8_ps,-Cp)
    Avion[7,0]=x_2_long(Vect_8ps[0,0],long_piste)
    Avion[7,1]=y_2_lat(Vect_8ps[1,0],lat_piste)
    Avion[7,2]=Vect_8ps[2,0]
    Avion[7,3]=t8_t7
    Avion[7,4]=t8
    Avion[7,5]=Ca8_p

    return nonNan(Avion)
