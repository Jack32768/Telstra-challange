//[sourcecode language="cpp"]

#include "Wire.h"
#include "ADXL345.h"
#include <Wire.h>
#include <L3G.h>

L3G gyro;
ADXL345 acc;
float d_xyz = 0.0;
double fXg = 0;
double fYg = 0;
double fZg = 0;
double a[3][7] = {0};//Acceleration data
double a1[2] = {0};//Final acceleration
double v0[2] = {0};//Initial velocity
double v1[2] = {0};//Final velocity
double d[2] = {0};//Displacement
int n = 6; //number of interval
//unsigned int delay_micros = 20000; // Time interval between each sampling（microsec）
//unsigned int delay_real = delay_micros - 2216;// Real delayed time in the program
int delay_interval = 32;
int delay_real = delay_interval - 2.1;
double delay_sec = delay_interval / 1000;
int x = 0, y = 1, z = 2;
int i = 0;
double simpson_c = delay_sec*3/8 / n;//Constant in Simpson's rule
float alpha_grav = 0.91;
float alpha = 0.5;
double gravity[3] = {0};
double g = 0;
double d_Gyro[3][7]={0};
double err_const = pow(delay_sec,4)/80;
//double err_const = 0;
char tmp[10] = {'\0'};
bool serialRdy() {
  //For Serial use only
  char inData[10];
  char inChar;
  String datas;
  int index = 0;
  while(1) {
    if (Serial.available() > 0) {
      inChar = Serial.read(); // Read a character
      inData[index] = inChar; // Store it
      index++; // Increment where to write next
      inData[index] = '\0'; // Null terminate the string
    }
    datas = inData;
    if (datas.indexOf("start") >= 0) {
      Serial.println("ready");
      return 1;
    }
    if (index >= 5) {
      inData[0] = (char)0;
      datas = "";
      index = 0;
    }
  }
}

void setup()
{
  acc.begin();
  acc.setRange(acc.RANGE_2G);
  //acc.setZeroG(0.02,0.01,0.01)
  acc.setZeroG(0.0,-0.00,0.0);
  Serial.begin(9600);
  Wire.begin();
  dtostrf(simpson_c, 5,4, tmp);
  Serial.println(tmp);
  if (!gyro.init())
  {
    Serial.println("Failed to autodetect gyro type!");
    while (1);
  }
  gyro.enableDefault();
  delay(100);
}

void loop()
{
  //Serial.print("Time: ");
  //int t1 = micros(), t2 = 0;
  if( i <= n){ //if more data needed
    
    /////////////////////////////////////////////////////////////////////////
    ////////////////////////Get the Acceleration data////////////////////////
    /////////////////////////////////////////////////////////////////////////
    double Xg, Yg, Zg;
    acc.read(&Xg, &Yg, &Zg);
    //Low Pass Filter to smooth out data
    fXg = fXg * alpha + (1 - alpha) * Xg;
    fYg = fYg * alpha + (1 - alpha) * Yg;
    fZg = fZg * alpha + (1 - alpha) * Zg;
    //Gravity filter (LPH)
    gravity[x] = alpha_grav * gravity[x] + (1 - alpha_grav) * fXg;
    gravity[y] = alpha_grav * gravity[y] + (1 - alpha_grav) * fYg;
    gravity[z] = alpha_grav * gravity[z] + (1 - alpha_grav) * fZg;
    g = 9.88*sqrt(pow(gravity[x],2)+pow(gravity[y],2)+pow(gravity[z],2));
    // Get the acceleration data
    a[x][i] =g*( fXg - gravity[x]);
    a[y][i] =g*( fYg - gravity[y]);
    //a[z][i] = fZg - gravity[z];
    //dtostrf(a[x][i], 5,4, tmp);
    //Serial.println(tmp);
    /////////////////////////////////////////////////////////////////////////
    ////////////////////////Get the Gyro data////////////////////////////////
    /////////////////////////////////////////////////////////////////////////
    
    //Get Gyro data
    gyro.read();
    d_Gyro[z][i] = getdps((int)gyro.g.z);
    if (abs(d_Gyro[z][i]) <= 0.7){
      d_Gyro[z][i] = 0;
    }
    //Serial.print(d_Gyro[z][i]);
    //dtostrf(d_Gyro[z][i], 5,4, tmp);
    //Serial.println(tmp);
    //Pass it through a LPF
    //d_Gyro[2][i] = getdps((int)gyro.g.z) * alpha + (d_Gyro[2][i] * (1 - alpha));  
    i++;
//N.B:2160microssecond to get there from the beginning of the loop
//Modify needed
    //t2 = micros();
    //Serial.print("TC");
    //Serial.println(t2-t1);
    //delay(1000);
    
    delay(delay_real);
  } else {  //if data enough
    int t1 = micros(), t2 = 0;
    i = 1;
    for (int q = 0; q <= 1; q++) {
      if (abs(a[q][5]) <= 1) {
        v0[q] = 0;
      }
    }
    //Simpson for Acc
    float acc_sum[2] = {0}, acc_avr[2] = {0};
    for(int ind = 0; ind < 7;ind++){
      acc_sum[x] += a[x][ind];
      acc_sum[y] += a[y][ind];
    }
    acc_avr[x] = acc_sum[x]/7;
    acc_avr[y] = acc_sum[y]/7;
    v1[x] = v0[x] + delay_interval*3/8*(a[x][0]+3*a[x][1]+3*a[x][2]+2*a[x][3]+3*a[x][4]+3*a[x][5]+a[x][6])/1000 - pow(delay_interval/1000,5) * 3 /80 * pow(acc_avr[x],4);
    v1[y] = v0[y] + delay_interval*3/8*(a[y][0]+3*a[y][1]+3*a[y][2]+2*a[y][3]+3*a[y][4]+3*a[y][5]+a[y][6])/1000 - pow(delay_interval/1000,5) * 3 /80 * pow(acc_avr[y],4);
    //v1[z] = v0[z] + c*(a[z][0]+3*a[z][1]+3*a[z][2]+2*a[z][3]+3*a[z][4]+3*a[z][5]+a[z][6]);
    //Serial.println(v1[x]);
    //Simpson for Gyro
    float gyro_sum = 0, gyro_avr = 0;
    for(int ind = 0; ind < 7;ind++){
      gyro_sum += d_Gyro[z][ind];
    }
    gyro_avr = gyro_sum / 7;
    d_xyz =  delay_interval*3.1667/8* (d_Gyro[z][0]+3*d_Gyro[z][1]+3*d_Gyro[z][2]+2*d_Gyro[z][3]+3*d_Gyro[z][4]+d_Gyro[z][5]+d_Gyro[z][6]);
    d_xyz = d_xyz/1000 - pow(delay_interval/1000,5) * 3 /80 * pow(gyro_avr,4);
    /*
    for(int j = 0; i < n+1; n++) {
    }
    */
    //Displacement
    d[x] = (v0[x]+v1[x])*delay_interval*3/1000;
    d[y] = (v0[y]+v1[y])*delay_interval/200;
    //d[z] = (v0[z]+v1[z])*dt/2;
    //update final velocity
    v0[x] = v1[x];
    v0[y] = v1[y];
    //v0[z] = v1[z];
    //Update initial accelerateion
    a[x][0] = a[x][n];
    a[y][0] = a[y][n];
    //a[z][0] = a[z][n];
    d_Gyro[z][0] = d_Gyro[z][n];
    //Serial.println(d_xyz);
    //serialRdy();//around 88*5microseconds needed
    //serialRdy()
    if (serialRdy()) {
      //Serial.println(g);
      Serial.print("[");
      Serial.print(d[x]);
      Serial.print(",");
      Serial.print(d[y]);
      Serial.print(",");
      Serial.print(d_xyz);
      Serial.println("];");  
  //Calculating used 1640+440 microsecond
    }
    //t2 = micros();
    //Serial.print("TC:");
    //Serial.println(t2-t1);
    //delay(1000);
  }
}

int getdps(int input) {
  //Scale up by 100
  return (input-10)*8.75/1000;
}

