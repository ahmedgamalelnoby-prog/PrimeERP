import {useCallback,useEffect,useState} from "react";
import {rentalsService} from "../services/rentals.service";
import type {RentalCharge,RentalContract} from "../types/rentals";
export function useRentals(){
 const [contracts,setContracts]=useState<RentalContract[]>([]);const [charges,setCharges]=useState<RentalCharge[]>([]);const [loading,setLoading]=useState(true);
 const reload=useCallback(async()=>{setLoading(true);try{const [c,ch]=await Promise.all([rentalsService.contracts(),rentalsService.charges()]);setContracts(c);setCharges(ch)}finally{setLoading(false)}},[]);
 useEffect(()=>{void reload()},[reload]);
 return {contracts,charges,loading,reload,activate:rentalsService.activate,terminate:rentalsService.terminate,charge:rentalsService.charge};
}
