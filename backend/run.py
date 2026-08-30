import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # إيقاف إعادة التحميل التلقائي في الإنتاج
        workers=4      # عدد العمال لتحسين الأداء
    )