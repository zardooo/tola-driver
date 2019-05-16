# initialize

# 记录数据的文件位置
path = '/opt/tola.data/'
# logger file
logger = '/var/log/tola.log'

# 采样中心频率                  (Hz)
center_freq = 97.5*1000*1000
# 中心频率误差修正              (ppm)
err_ppm = 50
# 采样率                        (Hz)
sample_rate = 2*1024*1024
# 带宽                          (MHz)
bandwidth = 2
# 放大器增益 (auto为自适应控制) (dB)
gain = 'auto'
# 0时为I/Q采样，置为1或2时只采一路
direct_samp = 0

# 单次采样的数据量大小 [每次采样点数， 采样时间(s)]
sample_size = [1024*1024, 1]

# 是否启用ipv4
if_ipv4 = True
# 是否启用ipv6
if_ipv6 = True
