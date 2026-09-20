import client from "@/shared/api/client";
const cid=()=>Number(localStorage.getItem("company_id"));
export const bankReconciliationApi={
 accounts:()=>client.get("/treasury/reconciliation/accounts",{params:{company_id:cid()}}),
 statements:(bank_account_id:number)=>client.get("/treasury/reconciliation/statements",{params:{company_id:cid(),bank_account_id}}),
 lines:(statement_id:number)=>client.get("/treasury/reconciliation/statements/"+statement_id+"/lines"),
};
