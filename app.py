from flask import Flask, render_template_string

app = Flask(__name__)

# بيانات تجريبية لقصص النجاح
success_stories = [
    {
        "name": "أحمد الرواد",
        "struggle": "واجه صعوبة بالغة في العثور على وظيفة بعد التخرج لعدم امتلاكه خبرة عمليّة، وكان يدرس في بيئة تفتقر للتوجيه.",
        "turning_point": "قرر التوقف عن اللوم، وبدأ بالتعلم الذاتي وبناء مشاريع حقيقية ورفعها على GitHub ليفهم السوق فعلياً.",
        "outcome": "أصبح الآن مهندس DevOps محترف يقود فريقاً تقنياً ويساعد المبتدئين في شق طريقهم."
    },
    {
        "name": "سارة علي",
        "struggle": "تعرض مشروعها الأول للفشل الخسير وخسرت كل رأس مالها بسبب ضعف التخطيط الأمني للموقع واختراقه.",
        "turning_point": "درست ثغرات مشروعها السابقة، وتعمقت في مفاهيم الـ DevSecOps لتأمين التطبيقات منذ السطر الأول للكود.",
        "outcome": "أسست منصتها الجديدة الحصينة، وتعمل حالياً كمستشارة في أمن المعلومات للمشاريع الناشئة."
    }
]

@app.route('/')
def home():
    html_template = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>منصة مسارات - قصص وتحديات</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f6f9; color: #333; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { text-align: center; color: #2c3e50; }
            .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-right: 5px solid #3498db; }
            .name { font-size: 1.4em; color: #2980b9; font-weight: bold; }
            .section-title { font-weight: bold; color: #c0392b; margin-top: 10px; }
            .success-title { font-weight: bold; color: #27ae60; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>منصة مسارات: قصص ملهمة في مواجهة التحديات</h1>
            <hr>
            {% for story in stories %}
            <div class="card">
                <div class="name">{{ story.name }}</div>
                <div class="section-title">مرحلة الصعوبة والتحدي:</div>
                <p>{{ story.struggle }}</p>
                <div class="success-title">نقطة التحول والنجاح:</div>
                <p>{{ story.turning_point }}</p>
                <p><strong>النتيجة الحالية:</strong> {{ story.outcome }}</p>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, stories=success_stories)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)