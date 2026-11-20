
import requests

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView

from drf_spectacular.utils import extend_schema

from app.orders.models import Order, Status
from ..models import Payment, PaymentStatus
from .serializer import PaymentInitiateSerializer


class PaymentInitiateView(GenericAPIView):
    serializer_class = PaymentInitiateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Payment",
        tags=["Payments"]
    )
    def post(self, request, *args, **kwargs):

        order_id = request.data.get("order_id")

        order = get_object_or_404(
            Order.objects.filter(user=request.user),
            pk=order_id,
        )

        if order.status != Status.PENDING:
            return Response(
                {"detail": "This order is not eligible for payment."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = Payment.objects.create(
            order=order,
            total_amount=order.total_amount,
        )

        amount_paisa = int(payment.total_amount * 100)

        payload = {
            "return_url": "https://shopease-backend-l1z2.onrender.com/api/payments/verify/",
            "website_url": "https://shopease-henna.vercel.app/",
            "amount": amount_paisa,
            "purchase_order_id": str(order.id),
            "purchase_order_name": f"Order {order.id}",
        }

        try:
            khalti_response = requests.post(
                "https://dev.khalti.com/api/v2/epayment/initiate/",
                headers={
                    "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=20,
            )

        except requests.exceptions.RequestException as error:
            print("KHALTI CONNECTION ERROR:", str(error))

            return Response(
                {"detail": "Unable to connect to Khalti."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if khalti_response.status_code != 200:
            print("KHALTI STATUS:", khalti_response.status_code)
            print("KHALTI ERROR:", khalti_response.text)

            return Response(
                {"detail": "Unable to initiate Khalti payment."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        try:
            response_data = khalti_response.json()

            pidx = response_data["pidx"]
            payment_url = response_data["payment_url"]

        except (ValueError, KeyError):
            print("INVALID KHALTI RESPONSE:", khalti_response.text)

            return Response(
                {"detail": "Invalid response received from Khalti."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        payment.pidx = pidx
        payment.status = PaymentStatus.INITIATED
        payment.save()

        return Response({
            "payment_url": payment_url,
            "pidx": pidx,
        })


class PaymentVerifyView(GenericAPIView):

    @extend_schema(
        summary="PaymentVerify",
        tags=["Payments"]
    )
    def get(self, request, *args, **kwargs):

        pidx = request.query_params.get("pidx")

        if not pidx:
            return Response(
                {"detail": "Missing payment identifier"},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = get_object_or_404(
            Payment.objects.filter(pidx=pidx)
        )

        if payment.status == PaymentStatus.COMPLETED:
            return redirect(
                f"https://shopease-henna.vercel.app/payment-result?status=success&order_id={payment.order_id}"
            )

        try:
            lookup_response = requests.post(
                "https://dev.khalti.com/api/v2/epayment/lookup/",
                headers={
                    "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "pidx": pidx
                },
                timeout=20,
            )

        except requests.exceptions.RequestException as error:
            print("KHALTI LOOKUP ERROR:", str(error))

            return Response(
                {"detail": "Unable to connect to Khalti. Please try again later."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        try:
            response_data = lookup_response.json()

        except ValueError:
            return Response(
                {"detail": "Khalti returned an invalid response."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        payment_status = response_data.get("status")

        if lookup_response.status_code == 400 and payment_status == "Expired":
            payment.status = PaymentStatus.EXPIRED
            payment.save()

            return Response(
                {"detail": "Payment link has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif lookup_response.status_code == 400 and payment_status == "User canceled":
            payment.status = PaymentStatus.CANCELLED
            payment.save()

            return Response(
                {"detail": "Payment was cancelled by the user."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if lookup_response.status_code != 200:
            print("KHALTI LOOKUP STATUS:", lookup_response.status_code)
            print("KHALTI LOOKUP RESPONSE:", lookup_response.text)

            return Response(
                {"detail": "Unable to verify payment with Khalti."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        khalti_amount = response_data.get("total_amount")
        expected_amount = int(payment.total_amount * 100)

        if payment_status == "Completed" and khalti_amount == expected_amount:

            with transaction.atomic():
                payment.status = PaymentStatus.COMPLETED
                payment.save()

                payment.order.status = Status.PAID
                payment.order.save()

            return redirect(
                f"https://shopease-henna.vercel.app/payment-result?status=success&order_id={payment.order_id}"
            )

        elif payment_status == "Completed" and khalti_amount != expected_amount:

            payment.status = PaymentStatus.AMOUNT_MISMATCH
            payment.save()

            return Response(
                {"detail": "Payment amount mismatch. Please contact support."},
                status=status.HTTP_400_BAD_REQUEST
            )

        elif payment_status == "Pending":

            payment.status = PaymentStatus.PENDING
            payment.save()

            return Response(
                {"detail": "Payment is pending. Please wait for confirmation."},
                status=status.HTTP_200_OK
            )

        elif payment_status == "Initiated":

            payment.status = PaymentStatus.INITIATED
            payment.save()

            return Response(
                {"detail": "Payment has been initiated. Awaiting confirmation."},
                status=status.HTTP_200_OK
            )

        elif payment_status == "Failed":

            payment.status = PaymentStatus.FAILED
            payment.save()

            return Response(
                {"detail": "Payment failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

        else:
            return Response(
                {"detail": "Payment is not completed. Order remains pending."},
                status=status.HTTP_502_BAD_GATEWAY
            )
