import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pvlib as pv
from tqdm import tqdm
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS as TMP
from pvlib import pvsystem, modelchain, location

# In[ ]:
class PV_system: # 설정값 저장용
    def __init__(self, name, region, tilt_angle , azimuth_angle, STC_power, loss):
        self.name = name
        self.region = region
        self.tilt_angle = tilt_angle
        self.azimuth_angle = azimuth_angle
        self.STC_power = STC_power
        self.loss = loss

# In[ ]:
def read_weather(filename_weather,datetime, solpos):
    df_weather = pd.read_csv(filename_weather, index_col=4, header=0,encoding='cp949')
    df_weather.columns = range(len(df_weather.columns))
    col_n = {i: j for i, j in zip(range(4, 16, 2), data_list)}
    df_weather = (df_weather.rename(columns=col_n)[data_list]).astype('f',errors='ignore')
    df_weather.index = datetime
    df_weather['dni'] = \
    pv.irradiance.disc(df_weather['ghi'], solpos['zenith'], datetime, pressure=df_weather['Pressure'] * 100)['dni']
    df_weather['dhi'] = df_weather['ghi'] - df_weather['dni'] * np.cos(np.radians(solpos['zenith']))
    df_weather = df_weather.fillna(0)
    return df_weather
def TransferIrradiance(surface_tilt, surface_azimuth, solpos, df_weather):
    ir_poa = pv.irradiance.get_total_irradiance(surface_tilt, surface_azimuth, solpos['zenith'], solpos['azimuth'], df_weather['dni'], df_weather['ghi'], df_weather['dhi'], dni_extra=1364.0, airmass=None, albedo=0.25, surface_type=None, model='perez', model_perez='allsitescomposite1990')
    return ir_poa.fillna(0)
def cal_power(ir_poa, df_weather, pdc0, gamma_pdc, temp_para):
#     temp_cell = pv.temperature.sapm_module(ir_poa, df_weather['Temperature'], df_weather['Wind-spd'], temp_para['a'], temp_para['b'])
    temp_cell = pv.temperature.fuentes(ir_poa, df_weather['Temperature'], df_weather['Wind-spd'], 50, module_height=5, wind_height=9.144,emissivity=0.84, absorption=0.83, surface_tilt=30, module_width=0.31579, module_length=1.2)
    power = pv.pvsystem.pvwatts_dc(ir_poa, temp_cell, pdc0 = pdc0, gamma_pdc = gamma_pdc, temp_ref=25.0)*(100-losses)/100
    return power, temp_cell

# In[ ]:
def main():
    regions=[(i.split('_')[-1]).split('.')[0] for i in weather_list]
    TMYs=[(i.split('/')[2]) for i in weather_list]
    df_merge = pd.DataFrame()
    for t_p in t_p_l:
        temp_para = TMP['sapm'][t_p]
        for t, a in zip(t_l, a_l):
            case = 'Tilt: ' + str(t) + 'º '+ 'Azimuth: ' +str(a) + 'º'
            for i_r in tqdm(range(len(regions))):
                reg, TMY = regions[i_r], TMYs[i_r]
                if reg == 'Jeju':
                    dt = datetime_jeju[TMY]
                else:
                    dt = datetime[TMY]
                PV_1 = PV_system(name=case, region=reg, tilt_angle=t, azimuth_angle=a, STC_power=STC_power, loss=losses)
                df_ = pd.DataFrame()
                solpos = pv.solarposition.get_solarposition(dt, latitude_dict[PV_1.region],
                                                            longitude_dict[PV_1.region])
                df_weather = read_weather([i for i in weather_list if PV_1.region in i][0], dt, solpos)
                df_['poa_global'] = TransferIrradiance(PV_1.tilt_angle, PV_1.azimuth_angle, solpos, df_weather)['poa_global']
                df_['DC_Power'], df_['Temperature'] = cal_power(df_['poa_global'], df_weather, PV_1.STC_power, g_, temp_para)
                df_['yield'] = df_['DC_Power'] / STC_power
                df_['efficiency'] = df_['DC_Power'] / df_['poa_global']
                df_['Temperature_Outdoor'] = df_weather['Temperature']
                df_['Temperature_Coefficient (%/C˚)'] = g_
                df_['type'] = t_p
                df_[['name', 'region', 'tilt_angle', 'azimuth_angle', 'TMY']] = PV_1.name, PV_1.region, str(PV_1.tilt_angle), str(PV_1.azimuth_angle), TMY
                df_['Time'] = pd.date_range(start='2012-01-01 00:00:00', end='2012-12-30 23:00:00', freq='1h')
                df_merge = pd.concat([df_merge, df_])
    df_merge = df_merge.reset_index(drop=True)
    df_merge['Month'] = df_merge['Time'].dt.month
    df_merge['Date'] = df_merge['Time'].dt.date
    df_merge['Hour'] = df_merge['Time'].dt.hour
    return df_merge

# In[ ]:
data_list = ['Temperature', 'Temp_Dew', 'RH', 'Pressure','Wind-spd', 'ghi']
region_en = ['Gangneung','Seoul', 'Daejeon', 'Daegu', 'Gwangju', 'Busan', 'Jeju',]
latitude_dict = {i:j for i,j in zip(region_en, [37.75, 37.57, 36.37, 35.88, 35.17, 35.1, 33.51])}
longitude_dict = {i:j for i,j in zip(region_en, [128.89, 126.97, 127.37, 128.65, 126.89, 129.03, 126.53])}
datetime = {'TMY(1991-2020)':pd.date_range(start='2012-01-01 00:00:00', end='2012-12-30 23:00:00', freq='1h',tz='Asia/Seoul') - pd.Timedelta('30min'), 'TMY(2008-2017)': pd.date_range(start='2012-01-01 00:00:00', end='2012-12-30 23:00:00', freq='1h',
                                            tz='Asia/Seoul')}
datetime_jeju = {'TMY(1991-2020)':pd.date_range(start='2012-01-01 00:00:00', end='2012-12-30 23:00:00', freq='1h', tz='Asia/Seoul') - pd.Timedelta('37min'), 'TMY(2008-2017)': pd.date_range(start='2012-01-01 00:00:00', end='2012-12-30 23:00:00', freq='1h',
                                            tz='Asia/Seoul')- pd.Timedelta('5min')}

# In[ ]:
# > ## 시뮬레이션 설정 조건 입력
# - weather_list: 기상데이터 경로(str)
# - t_p_l, t_l, a_l : 모듈 설치 유형(str), 설치경사각(˚), 설치 방위각(˚) (input type : list)
# - g_, STC_power, losses: 모듈 온도계수(1/℃), 단위면적기준 STC 출력(W/m2), 발전 손실률(%) (input type : float)

weather_list = ['./Data-Weather/TMY(1991-2020)/108_Seoul.csv',
                './Data-Weather/TMY(2008-2017)/976_Jeju.csv',
               ]
t_p_l = ['close_mount_glass_glass']
t_l, a_l, =[90, 90], [180, 90]
g_, STC_power = -0.004, 180
losses = pv.pvsystem.pvwatts_losses()

# > ## **Run(df_merge에 저장될거임)**

# In[ ]:
df_merge = pd.DataFrame()
if __name__ == '__main__':
    df_merge = main()

# In[ ]:
df_ = df_merge[df_merge['region']== 'Seoul']
df_s = pd.pivot_table(data=df_, index=['type', 'name','region', 'tilt_angle', 'azimuth_angle', 'TMY', 'Month'], values=['poa_global', 'DC_Power', 'Temperature', 'yield', 'efficiency','Temperature_Outdoor'], aggfunc='sum').reset_index()
df_d = pd.pivot_table(data=df_, index=['type', 'name','region', 'tilt_angle', 'azimuth_angle', 'TMY', 'Month','Date'], values=['poa_global', 'DC_Power', 'Temperature', 'yield', 'efficiency','Temperature_Outdoor'], aggfunc='sum').reset_index()
fig0, ax = plt.subplots(2,2, figsize=(14,10))
sns.barplot(data=df_s, x='Month', y='poa_global', hue='name', ax = ax[0][0])
ax[0][0].set(ylabel='Monthly Irradiation [Wh/Wp·month]')
sns.boxplot(data=df_d, x='Month',y='poa_global', hue='name', ax = ax[0][1])
ax[0][1].set(ylabel='Daily Irradiation [Wh/Wp·day]')
sns.scatterplot(data=df_,x='poa_global', y='poa_global', hue = 'name',ax = ax[1][0])
ax[1][0].set(xlabel='Poa_global', ylabel='Hourly Irradiation [Wh/Wp·hour]')
sns.lineplot(data=df_, x='Hour', y='poa_global', hue='name', ax = ax[1][1])
ax[1][1].set(ylabel='Mean Irradiation [Wh/Wp·hour]')

# In[ ]: Result View - Temperature
df_ = df_merge[df_merge['region']== 'Seoul']
fig1, ax = plt.subplots(2,2, figsize=(14,10))
sns.histplot(data=df_[(df_['Hour']>6) & (df_['Hour']<19)], kde=True, x='Temperature', hue='name',bins=30, ax = ax[0][0])
sns.boxplot(data=df_, x='Month', y='Temperature', hue='name', ax = ax[0][1])
sns.scatterplot(data=df_,x='poa_global', y='Temperature', hue = 'name',ax = ax[1][0])
ax[1][0].set(xlabel='poa_global')
sns.lineplot(data=df_, x='Hour', y='Temperature', hue='name', ax = ax[1][1])
ax[1][1].set(ylabel='poa_global')



# In[ ]: Result View - Power
df_ = df_merge[df_merge['region']== 'Seoul']
df_s = pd.pivot_table(data=df_, index=['type', 'name','region', 'tilt_angle', 'azimuth_angle', 'TMY', 'Month'], values=['poa_global', 'DC_Power', 'Temperature', 'yield', 'efficiency','Temperature_Outdoor'], aggfunc='sum').reset_index()
df_d = pd.pivot_table(data=df_, index=['type', 'name','region', 'tilt_angle', 'azimuth_angle', 'TMY', 'Month','Date'], values=['poa_global', 'DC_Power', 'Temperature', 'yield', 'efficiency','Temperature_Outdoor'], aggfunc='sum').reset_index()
fig2, ax = plt.subplots(2,2, figsize=(14,10))
sns.barplot(data=df_s, x='Month', y='yield', hue='name', ax = ax[0][0])
ax[0][0].set(ylabel='Monthly yield [kWh/kWp·month]')
sns.boxplot(data=df_d, x='Month',y='yield', hue='name', ax = ax[0][1])
ax[0][1].set(ylabel='Daily yield [kWh/kWp·day]')
sns.scatterplot(data=df_,x='poa_global', y='yield', hue = 'name',ax = ax[1][0])
ax[1][0].set(xlabel='Poa_global', ylabel='Hourly yield [kWh/kWp·hour]')
sns.lineplot(data=df_, x='Hour', y='yield', hue='name', ax = ax[1][1])
ax[1][1].set(ylabel='Mean hourly yield [kWh/kWp·hour]')
