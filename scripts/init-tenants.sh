#!/bin/bash
# Wait for the backend to be healthy
echo "Waiting for backend to be ready..."
until curl -s http://backend:8000/health | grep -q '"status":"healthy"'; do
    sleep 2
done
echo "Backend is ready!"

# Create T-Corp tenant
echo "Creating T-Corp tenant..."
curl -s -X POST http://backend:8000/api/v1/auth/register/company \
    -H "Content-Type: application/json" \
    -d '{
        "company_name": "T-Corp Industries",
        "subdomain": "tcorp",
        "company_email": "admin@tcorp.com",
        "company_phone": "+91-9876543210",
        "admin_email": "admin@tcorp.com",
        "admin_password": "TcorpAdmin123!",
        "admin_first_name": "Tech",
        "admin_last_name": "Admin",
        "timezone": "Asia/Kolkata",
        "country": "India"
    }' | head -c 500
echo ""

# Create A-Corp tenant
echo "Creating A-Corp tenant..."
curl -s -X POST http://backend:8000/api/v1/auth/register/company \
    -H "Content-Type: application/json" \
    -d '{
        "company_name": "A-Corp Solutions",
        "subdomain": "acorp",
        "company_email": "admin@acorp.com",
        "company_phone": "+91-9876543211",
        "admin_email": "admin@acorp.com",
        "admin_password": "AcorpAdmin123!",
        "admin_first_name": "Alpha",
        "admin_last_name": "Admin",
        "timezone": "Asia/Kolkata",
        "country": "India"
    }' | head -c 500
echo ""

echo ""
echo "=========================================="
echo "Sample tenants created!"
echo "=========================================="
echo ""
echo "T-Corp:"
echo "  Domain: tcorp.samvit.bhanu.dev"
echo "  Admin:  admin@tcorp.com / TcorpAdmin123!"
echo ""
echo "A-Corp:"
echo "  Domain: acorp.samvit.bhanu.dev"
echo "  Admin:  admin@acorp.com / AcorpAdmin123!"
echo "=========================================="
