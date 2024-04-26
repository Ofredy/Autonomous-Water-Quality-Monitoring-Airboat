/*

cpp_header.h*
Created on: Jan 8, 2024
Author: danie
*/

#ifndef MAIN_CPP_HEADERH
#define MAIN_CPP_HEADERH

#ifdef __cplusplus
extern "C" {
#endif
	int getMedianNum(int bArray[], int iFilterLen);
	int getMeanNum(int bArray[], int iFilterLen);
    void TDS_setup_function();
    void PH_setup_function();
    void Turbidity_setup_function();
    float TDS_function(float temperature);
    float PH_function(float temperature);
    float Turbidity_function();
    extern volatile float sharedTDSValue;
    extern volatile float cTemp;
    extern volatile float turbidity;
    extern volatile float phValue;
#ifdef __cplusplus
}
#endif



#endif /* MAIN_CPP_HEADERH */
