SELECT current_database(), current_user, version();

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'sales_documents'
  AND column_name IN ('company_id', 'number', 'document_type')
ORDER BY column_name;

SELECT company_id, number, COUNT(*) AS invoice_count
FROM public.sales_documents
WHERE document_type = 'invoice'
GROUP BY company_id, number
HAVING COUNT(*) > 1
ORDER BY invoice_count DESC
LIMIT 25;
