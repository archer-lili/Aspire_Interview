# Aspire_Interview

admin is precreated with username admin password admin
only admin can delete add edit records

A simple media management web app built with Flask and SQLAlchemy.  
Users can browse, manage, and track media content (like movies, books, or games), with role-based access for admins.

---

## 🚀 Features

- User authentication (Login/Register)
- Browse and search all media entries
- Admins can add, edit, and delete media
- Users can update media status: `owned`, `wishlist`, `currently using`, `completed`
- recommend engine using sentence transformers

---

## 🛠️ Setup Instructions

clone repo then,

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
