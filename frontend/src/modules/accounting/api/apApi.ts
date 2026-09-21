import client from "@/shared/api/client";
const company=()=>{const n=Number(localStorage.getItem("company_id"));if(!Number.isInteger(n)||n<=0)throw new Error("اختر شركة فعالة أولاً.");return n};
export const apApi={
 aging:(partnerId:number,asOf?:string)=>client.get("/ap/suppliers/"+partnerId+"/aging",{params:{company_id:company(),...(asOf?{as_of:asOf}:{})}}),
 statement:(partnerId:number,fromDate?:string,toDate?:string,asOf?:string)=>client.get("/ap/suppliers/"+partnerId+"/statement",{params:{company_id:company(),...(fromDate?{from_date:fromDate}:{}),...(toDate?{to_date:toDate}:{}),...(asOf?{as_of:asOf}:{})}}),
 reconcile:(partnerId?:number,asOf?:string)=>client.post("/ap/reconcile",{company_id:company(),partner_id:partnerId,as_of:asOf,persist:true}),
 threeWay:(billId:number,tolerance=0)=>client.get("/ap/three-way-match/"+billId,{params:{company_id:company(),tolerance}}),
 writeOffs:(status?:string)=>client.get("/ap/write-offs",{params:{company_id:company(),...(status?{status}:{})}}),
 decideWriteOff:(id:number,approve:boolean,reason?:string)=>client.post("/ap/write-offs/"+id+"/decision",{company_id:company(),approve,reason}),
 variances:(status?:string)=>client.get("/ap/variances",{params:{company_id:company(),...(status?{status}:{})}}),
 decideVariance:(id:number,approve:boolean,waive=false,reason?:string)=>client.post("/ap/variances/"+id+"/decision",{company_id:company(),approve,waive,reason}),
 unapplied:(paymentId:number)=>client.get("/ap/payments/"+paymentId+"/unapplied",{params:{company_id:company()}})
};