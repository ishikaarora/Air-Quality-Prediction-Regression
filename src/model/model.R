library(Amelia)
library(dplyr)

weather <- read.csv("data/EPA_weather_2016.csv")
weather_na <- weather %>% filter(!is.na(Average.Air.Pressure))
length(unique(weather$County))

data <- read.csv("data/data_merged_meso_weather-dropped.csv")

mod <- lm(AQI ~ Temperature + Altimeter + Precipitation_24hrAccum + RelHumidity + WindSpeed + Total.Emissions + CO2 + Methane + Nitrous.Oxide + HFC + PFC + SF6 + NF3 + HFE + Short.Lived.Compounds + Income + Population + pp_net_gen_MWh, data=data)
summary(mod)

sapply(data,function(x) sum(is.na(x)))
sapply(data$Region,function(x) unique(x, na.rm=TRUE))

max(data$Region, na.rm = TRUE)
missmap(data, main = "Missing values vs observed")

rm(data)

bk <- read.csv("data/weather_data_berkshire.csv")
bk1 <- read.csv("data/weather_data_berkshire1.csv")

bk2 <- weather %>% filter(state.name)
sapply(bk,function(x) sum(is.na(x)))
sapply(bk1,function(x) sum(is.na(x)))

bk$altimeter_set_1 - bk1$altimeter_set_1
