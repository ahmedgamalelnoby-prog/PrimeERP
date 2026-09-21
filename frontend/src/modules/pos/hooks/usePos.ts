import { useCallback, useState } from "react";
import { toast } from "react-hot-toast";

export function usePosAction<T extends (...args:any[]) => Promise<any>>(action:T) {
  const [loading,setLoading]=useState(false);
  const execute=useCallback(async (...args:Parameters<T>)=>{
    setLoading(true);
    try { return await action(...args); }
    catch(error:any) { toast.error(error?.response?.data?.detail ?? "تعذر تنفيذ العملية."); throw error; }
    finally { setLoading(false); }
  },[action]);
  return { execute, loading };
}
