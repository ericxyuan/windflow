#include "Control.h"
namespace wf {
Fault escSafetyFault(const Settings& s,const Inputs& in){
 if(!in.escTelemetryValid||!isfinite(in.rpm)||!isfinite(in.escFetC)||!isfinite(in.escInputA)||!isfinite(in.escPhaseA)||!isfinite(in.escDuty)||!isfinite(in.escVoltage))return Fault::EscTelemetry;
 if(in.escFault)return Fault::EscController;
 if(in.rpm< -50||in.escDuty< -.02f||in.escInputA< -.10f)return Fault::ReverseRotation;
 // 5000 RPM is an analysis ceiling, not a certified operating limit.
 if(in.rpm>fminf(kRotorAnalysisCeilingRpm,s.rpmAtMax*1.10f))return Fault::Overspeed;
 if(in.escFetC>=s.tripC)return Fault::Overtemperature;
 if(in.escVoltage<14||in.escVoltage>16||fabsf(in.escVoltage-in.busV)>1)return Fault::Power;
 if(in.escInputA>s.escInputLimitA||fabsf(in.escPhaseA)>s.escPhaseLimitA||in.escInputA*in.escVoltage>s.escPowerLimitW)return Fault::MotorCurrent;
 return Fault::None;
}
}
