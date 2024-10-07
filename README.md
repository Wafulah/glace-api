# Glace

Glace is a software designed for pharmacies and chemists to manage their inventory, customers, and record orders and purchases. It also includes a dashboard for monitoring performance metrics.

## Prerequisites

- python (version 3.12)
- Nextjs (version 14)

## Installation

1. Clone the repository: `git clone https://github.com/Wafulah/glace-api.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Clone the frontend repository: `git clone https://github.com/Wafulah/glace.git`
4. Install dependencies: `npm install`

## Usage

- To start Glace, run `npm run dev` for the frontend.
- Run `python manage.py runserver` for the backend.
- Or access the application through your web browser at [https://glace-store.vercel.app](https://glace-store.vercel.app).

## Initial Setup

### Login:

- You will be asked to log in and receive an email if successful.

### Set Up Store:

- Upon login, you will be prompted to set up a store. Input the name of your store (chemist or pharmacy).
- You will then get access to a dashboard.

### County and Category Setup:

- First, check if your county exists. If not, register it on the counties page.
- Then check categories and register them too.

### Customer Registration:

- Register your customers.

### Product Management:

- Move to products and fill in the products that exist in your store.
- You can update price,quantities amont other fields.

### Order Management:

- Select orders to input order details.
- After inputting order details, press "Select Order Items" and a pop-up will show.
- Select the product, fill in the details, then press "Continue". (If you don't press "Continue", the product won't be saved.)
- After you're done, press "Done" and then "Submit Order".

#### Notifications and Order Integrity

- A text message and email will be sent after order creation to the user.
- For integrity, only "Is Delivered," "Is Paid," and "Delivery Date" can be altered on the order detail page.   

## Features

- Inventory Management: Maintain and update details of stock including quantities,price etc.
- Customer Management: Manage customer information and track interactions.
- Order and Purchase Records: Record and track orders placed and purchases made.
- Performance Dashboard: Monitor key performance indicators (KPIs) and metrics through an intuitive dashboard.

## Configuration

### Backend Configuration

- This application uses `django-oidc-provider` as an OpenID Connect provider for authentication.
- Google Sign-In is integrated with django-oidc-provider to authenticate users.
- This application uses `neon` as its PostgreSQL database.

### Frontend Configuration

- The frontend of this application utilizes authjs for robust double authentication.
- During authentication, details retrieved from `Google` via `django-oidc-provider` are used as credentials to sign in the user on the frontend.

### Communication Between Backend and Frontend

- The backend (`django-oidc-provider`) provides user information and a session token upon successful authentication.
- This token is used to keep user logged in through sessions.
- `Simple_jwt` provides a JWT token whenever get-user-by-id is queried.
- This JWT token is used by the frontend (`Next.js`) to authorize API access.

### Token Management and Session Handling

- Next.js (using `authjs`) regularly queries an endpoint to ensure the JWT token is up-to-date and hasn't expired.
- Sessions are used to keep the user logged in, ensuring a seamless user experience.

## Additional Information

#### Assumptions

- A lot of data processing is done by the frontend; hence, the backend only checks for crucial data errors.

#### To-Do

- Improve error handling to capture more specific errors.
- Only tests for orders are currently being carried out; more tests need to be written later.
- Improve CI/CD checks and validation.

#### Notes

- This is just a basic setup upon which more advanced features can be built.

## Credits

## This project uses several open-source packages and frameworks:

- Django
- Django REST framework
- djangorestframework-simplejwt
- django-oidc-provider

- Next.js
- Authjs
- Shadcn 

- Neon database

- Vercel
- Render

## Contact

- For questions or support, contact [Victor Wafula](wafulahvictor@email.com).
