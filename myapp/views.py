from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer


from .models import CustomerUser, HealthRecord
from .forms import RegisterForm, LoginForm, EditProfileForm, HealthRecordForm, HealthRecordImportForm

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
import plotly.express as px
import plotly.offline as opy

# =========================
# AUTHENTICATION VIEWS
# =========================
def index(request):
    return render(request, 'index.html')

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. Please login.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = CustomerUser.objects.get(username=username)
                if user.status != 'active':
                    messages.error(request, "Your account is not active. Please contact support.")
                elif check_password(password, user.password):
                    request.session['user_id'] = user.user_id
                    request.session['username'] = user.username
                    messages.success(request, f"Welcome {user.username}!")
                    return redirect('dashboard')
                else:
                    messages.error(request, "Invalid password")
            except CustomerUser.DoesNotExist:
                messages.error(request, "User not found")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('index')


# =========================
# DASHBOARD VIEW WITH AI & PLOTLY
# =========================
def dashboard_view(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')

    user = CustomerUser.objects.get(user_id=request.session['user_id'])
    records = HealthRecord.objects.filter(user=user).order_by('date')

    prediction_result = None
    alerts = []
    recommendations = []
    chart = None

    if records.exists():
        # =========================
        # Convert Health Records to DataFrame
        # =========================
        df = pd.DataFrame(list(records.values(
            'weight', 'systolic_bp', 'diastolic_bp', 'sugar_level',
            'sleep_hours', 'exercise_minutes', 'stress_level', 'date'
        )))

        features = ['weight','systolic_bp','diastolic_bp','sugar_level','sleep_hours','exercise_minutes','stress_level']
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df[features])

        # Labels for disease risk
        y_diabetes = (df['sugar_level'] > 140).astype(int)
        y_hypertension = ((df['systolic_bp'] > 130) | (df['diastolic_bp'] > 80)).astype(int)

        # =========================
        # Incremental / Adaptive Learning
        # =========================
        # Load previous model state from session if exists
        if request.session.get('diabetes_model'):
            lr_model = LogisticRegression()
            lr_model.coef_ = np.array(request.session['diabetes_model']['coef'])
            lr_model.intercept_ = np.array(request.session['diabetes_model']['intercept'])
            lr_model.classes_ = np.array([0,1])
            lr_model.n_features_in_ = X_scaled.shape[1]
        else:
            lr_model = LogisticRegression()

        if len(np.unique(y_diabetes)) > 1:
            lr_model.fit(X_scaled, y_diabetes)  # retrain/adapt model
            # save model weights in session for next incremental update
            request.session['diabetes_model'] = {
                'coef': lr_model.coef_.tolist(),
                'intercept': lr_model.intercept_.tolist()
            }

        if request.session.get('hypertension_model'):
            dt_model = DecisionTreeClassifier(max_depth=4)
            dt_model.classes_ = np.array([0,1])
        else:
            dt_model = DecisionTreeClassifier(max_depth=4)

        if len(np.unique(y_hypertension)) > 1:
            dt_model.fit(X_scaled, y_hypertension)
            request.session['hypertension_model'] = True  # flag stored

        # =========================
        # Predict last record risk
        # =========================
        diabetes_risk_prob = lr_model.predict_proba(X_scaled)[:,1][-1] if len(np.unique(y_diabetes))>1 else y_diabetes.values[-1]
        hypertension_risk_prob = dt_model.predict_proba(X_scaled)[:,1][-1] if len(np.unique(y_hypertension))>1 else y_hypertension.values[-1]

        def risk_level(prob):
            if prob < 0.3:
                return 'Low'
            elif prob < 0.7:
                return 'Medium'
            else:
                return 'High'

        prediction_result = {
            'diabetes': risk_level(diabetes_risk_prob),
            'hypertension': risk_level(hypertension_risk_prob),
            'diabetes_prob': round(diabetes_risk_prob*100,1),
            'hypertension_prob': round(hypertension_risk_prob*100,1)
        }

        # =========================
        # Alerts & Recommendations
        # =========================
        latest = df.iloc[-1]
        if latest['systolic_bp'] > 180 or latest['diastolic_bp'] > 120:
            alerts.append("Dangerously high blood pressure!")
        if latest['sugar_level'] > 200:
            alerts.append("Critical sugar level detected!")
        if latest['stress_level'] >= 9:
            alerts.append("High stress level alert!")

        if prediction_result['diabetes'] != 'Low':
            recommendations.append("Monitor sugar intake and maintain regular glucose checks.")
        if prediction_result['hypertension'] != 'Low':
            recommendations.append("Reduce salt intake and exercise daily to manage blood pressure.")
        if latest['sleep_hours'] < 6:
            recommendations.append("Increase sleep duration for better health.")
        if latest['exercise_minutes'] < 30:
            recommendations.append("Include at least 30 minutes of exercise daily.")

        # =========================
        # Plotly Health Trends
        # =========================
        fig = px.line(df, x='date', y=['weight','systolic_bp','diastolic_bp','sugar_level','sleep_hours'],
                      labels={'value':'Measurement','variable':'Metric','date':'Date'},
                      title='Health Trends Over Time')
        fig.update_layout(height=400, template='plotly_white')
        chart = opy.plot(fig, auto_open=False, output_type='div')
    else:
        alerts.append("No health records found. Add your first record to start predictions.")

    return render(request, 'dashboard.html', {
        'user': user,
        'prediction_result': prediction_result,
        'alerts': alerts,
        'recommendations': recommendations,
        'chart': chart
    })


# =========================
# PROFILE MANAGEMENT
# =========================
def edit_profile(request):
    if not request.session.get('user_id'):
        messages.error(request, "You need to log in first.")
        return redirect('login')

    user = get_object_or_404(CustomerUser, pk=request.session['user_id'])
    if request.method == 'POST':
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('dashboard')
    else:
        form = EditProfileForm(instance=user)

    return render(request, 'edit_profile.html', {'form': form, 'user': user})


# =========================
# HEALTH RECORDS CRUD
# =========================
def health_records_list(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')
    user = CustomerUser.objects.get(user_id=request.session['user_id'])
    records = HealthRecord.objects.filter(user=user).order_by('-date')
    return render(request, 'list.html', {'records': records, 'user': user})

def health_record_create(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')
    if request.method == "POST":
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user_id = request.session['user_id']
            record.save()
            messages.success(request, "Health record added successfully.")
            return redirect('health_records_list')
    else:
        form = HealthRecordForm()
    return render(request, 'form.html', {'form': form, 'title': 'Add Health Record'})

def health_record_edit(request, record_id):
    record = get_object_or_404(HealthRecord, pk=record_id, user_id=request.session['user_id'])
    if request.method == "POST":
        form = HealthRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Health record updated successfully.")
            return redirect('health_records_list')
    else:
        form = HealthRecordForm(instance=record)
    return render(request, 'form.html', {'form': form, 'title': 'Edit Health Record'})

def health_record_delete(request, record_id):
    record = get_object_or_404(HealthRecord, pk=record_id, user_id=request.session['user_id'])
    record.delete()
    messages.success(request, "Health record deleted successfully.")
    return redirect('health_records_list')


# =========================
# IMPORT HEALTH RECORDS
# =========================
def health_record_import(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')

    if request.method == "POST":
        form = HealthRecordImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            try:
                df = pd.read_excel(file) if file.name.endswith(('xls','xlsx')) else pd.read_csv(file)
                required_cols = ['date', 'weight', 'systolic_bp', 'diastolic_bp', 'sugar_level', 'sleep_hours', 'exercise_minutes', 'stress_level']
                if not all(col in df.columns for col in required_cols):
                    messages.error(request, f"File must contain columns: {', '.join(required_cols)}")
                    return redirect('health_record_import')
                user = CustomerUser.objects.get(user_id=request.session['user_id'])
                for _, row in df.iterrows():
                    try:
                        HealthRecord.objects.create(
                            user=user,
                            date=row['date'],
                            weight=float(row['weight']),
                            systolic_bp=int(row['systolic_bp']),
                            diastolic_bp=int(row['diastolic_bp']),
                            sugar_level=float(row['sugar_level']),
                            sleep_hours=float(row['sleep_hours']),
                            exercise_minutes=int(row['exercise_minutes']),
                            stress_level=int(row['stress_level'])
                        )
                    except Exception:
                        continue
                messages.success(request, "Health records imported successfully.")
                return redirect('health_records_list')
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = HealthRecordImportForm()
    return render(request, 'import.html', {'form': form})


# =========================
# REPORTS AND EXPORTS
# =========================
def reports_view(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')

    user = CustomerUser.objects.get(user_id=request.session['user_id'])
    records = HealthRecord.objects.filter(user=user).order_by('date')
    
    trend = request.GET.get('trend','daily')
    chart = None
    summary = {}

    if records.exists():
        df = pd.DataFrame(list(records.values()))
        df['date'] = pd.to_datetime(df['date'])
        if trend == 'weekly':
            df_resampled = df.set_index('date').resample('W').mean().reset_index()
        elif trend == 'monthly':
            df_resampled = df.set_index('date').resample('M').mean().reset_index()
        else:
            df_resampled = df.copy()

        fig = px.line(df_resampled, x='date', y=['weight','systolic_bp','diastolic_bp','sugar_level','sleep_hours'],
                      labels={'value':'Measurement','variable':'Metric','date':'Date'},
                      title=f'Health Trends ({trend.capitalize()})')
        fig.update_layout(height=400, template='plotly_white')
        chart = opy.plot(fig, auto_open=False, output_type='div')

        for metric in ['weight','systolic_bp','diastolic_bp','sugar_level','sleep_hours']:
            if len(df_resampled) >= 2:
                change = df_resampled[metric].iloc[-1] - df_resampled[metric].iloc[0]
                summary[metric] = f"{'Increased' if change>0 else 'Decreased' if change<0 else 'No change'} by {abs(round(change,2))}"
            else:
                summary[metric] = "Not enough data"

    return render(request, 'reports.html', {'user': user,'chart': chart,'summary': summary,'trend': trend})


def export_csv(request):
    """
    Export user's health records to CSV
    """
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')

    user = CustomerUser.objects.get(user_id=request.session['user_id'])
    records = HealthRecord.objects.filter(user=user).order_by('date')
    if not records.exists():
        messages.error(request, "No records to export.")
        return redirect('reports')

    df = pd.DataFrame(list(records.values()))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{user.username}_health_records.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response


def export_excel(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')

    user = CustomerUser.objects.get(user_id=request.session['user_id'])
    records = HealthRecord.objects.filter(user=user).order_by('date')

    if not records.exists():
        messages.error(request, "No health records to export.")
        return redirect('health_records_list')

    # Convert records to DataFrame
    df = pd.DataFrame(list(records.values()))
    
    # Make datetime columns timezone-naive
    for col in ['date', 'created_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.tz_localize(None)

    # Export to Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Health_Records_{user.username}.xlsx'

    df.to_excel(response, index=False)
    return response

def generate_pdf(request):
    if 'user_id' not in request.session:
        return redirect('login')

    if request.method == "POST":
        user = CustomerUser.objects.get(user_id=request.session['user_id'])
        trend = request.POST.get('trend', 'daily')
        records = HealthRecord.objects.filter(user=user).order_by('date')

        if not records.exists():
            return HttpResponse("No health data to generate report.")

        # Convert records to DataFrame
        df = pd.DataFrame(list(records.values()))
        df['date'] = pd.to_datetime(df['date'])

        # Resample for weekly/monthly trend
        if trend == 'weekly':
            df = df.set_index('date').resample('W').mean().reset_index()
        elif trend == 'monthly':
            df = df.set_index('date').resample('M').mean().reset_index()

        # Generate summary
        summary = []
        for metric in ['weight','systolic_bp','diastolic_bp','sugar_level','sleep_hours']:
            if len(df) >= 2:
                change = df[metric].iloc[-1] - df[metric].iloc[0]
                trend_text = f"{'Increased' if change>0 else 'Decreased' if change<0 else 'No change'} by {abs(round(change,2))}"
            else:
                trend_text = "Not enough data"
            summary.append([metric.capitalize(), trend_text])

        # ========================
        # Create PDF
        # ========================
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Health_Report_{trend}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(f"{user.full_name}'s Health Report ({trend.capitalize()})", styles['Title']))
        elements.append(Spacer(1, 20))

        # Trend Summary Table
        elements.append(Paragraph("Trend Summary:", styles['Heading2']))
        table = Table(summary, colWidths=[200, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        # Detailed Health Records Table
        elements.append(Paragraph("Detailed Health Records:", styles['Heading2']))
        df_table = df[['date','weight','systolic_bp','diastolic_bp','sugar_level','sleep_hours','exercise_minutes','stress_level']]
        data = [df_table.columns.tolist()] + df_table.values.tolist()
        table2 = Table(data, repeatRows=1)
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ]))
        elements.append(table2)

        doc.build(elements)
        return response

    return redirect('reports')