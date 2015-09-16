/* --------------------------------------------------------------------------------
 #
 #	4DPlugin.cpp
 #	source generated by 4D Plugin Wizard
 #	Project : Split Pictures
 #	author : miyako
 #	2015/09/17
 #
 # --------------------------------------------------------------------------------*/


#include "4DPluginAPI.h"
#include "4DPlugin.h"

void PluginMain(PA_long32 selector, PA_PluginParameters params)
{
	try
	{
		PA_long32 pProcNum = selector;
		sLONG_PTR *pResult = (sLONG_PTR *)params->fResult;
		PackagePtr pParams = (PackagePtr)params->fParameters;

		CommandDispatcher(pProcNum, pResult, pParams); 
	}
	catch(...)
	{

	}
}

void CommandDispatcher (PA_long32 pProcNum, sLONG_PTR *pResult, PackagePtr pParams)
{
	switch(pProcNum)
	{
// --- Split Pictures

		case 1 :
			SPLIT_PICTURES(pResult, pParams);
			break;

	}
}

// -------------------------------- Split Pictures --------------------------------


void SPLIT_PICTURES(sLONG_PTR *pResult, PackagePtr pParams)
{
    PA_Picture Param1 = *(PA_Picture *)(pParams[0]);
	PA_Variable Param2 = *((PA_Variable*) pParams[1]);
	PA_Variable Param3 = *((PA_Variable*) pParams[2]);

	switch (Param2.fType)
	{
		case eVK_ArrayUnicode:
			break;
		case eVK_Undefined:
			PA_ClearVariable(&Param2);
			Param2 = PA_CreateVariable(eVK_ArrayUnicode);
			break;				
		default:
			break;
	}
    
	switch (Param3.fType) 
	{
		case eVK_ArrayPicture:
			break;
		case eVK_Undefined:
			PA_ClearVariable(&Param3);				
			Param3 = PA_CreateVariable(eVK_ArrayPicture);
			break;				
		default:
			break;
	}	
	
	if((Param2.fType == eVK_ArrayUnicode) && (Param3.fType == eVK_ArrayPicture)){

		PA_ResizeArray(&Param2, 0);
		PA_ResizeArray(&Param3, 0);
		
		unsigned int i = 0;
        
		PA_ErrorCode err = eER_NoErr;
		PA_Unistring type;
		
		while (err == eER_NoErr){
            i++;
            type = PA_GetPictureData(Param1, i, 0);
            err = PA_GetLastError();
            if(err == eER_NoErr){
                PA_Handle h = PA_NewHandle(0);
				PA_GetPictureData(Param1, i, h);
                err = PA_GetLastError();
                if(err == eER_NoErr){
                    PA_Picture picture = PA_CreatePicture(PA_LockHandle(h), PA_GetHandleSize(h));
                    PA_ResizeArray(&Param2, i);
                    PA_ResizeArray(&Param3, i);
                    PA_SetStringInArray(Param2, i, &type);
                    PA_SetPictureInArray(Param3, i, picture);
					PA_UnlockHandle(h);
                }
                PA_DisposeHandle(h);
            }			
		}
		
		PA_Variable *param2 = ((PA_Variable *)pParams[1]);
		
		param2->fType = Param2.fType;
		param2->fFiller = Param2.fFiller;
		param2->uValue.fArray.fCurrent = Param2.uValue.fArray.fCurrent;
		param2->uValue.fArray.fNbElements = Param2.uValue.fArray.fNbElements;
		param2->uValue.fArray.fData = Param2.uValue.fArray.fData;
        
		PA_Variable *param3 = ((PA_Variable *)pParams[2]);
		
		param3->fType = Param3.fType;
		param3->fFiller = Param3.fFiller;
		param3->uValue.fArray.fCurrent = Param3.uValue.fArray.fCurrent;
		param3->uValue.fArray.fNbElements = Param3.uValue.fArray.fNbElements;
		param3->uValue.fArray.fData = Param3.uValue.fArray.fData;
	}
}
