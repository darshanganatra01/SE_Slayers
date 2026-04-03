# ── Model registry ────────────────────────────────────────────────
# Import every model here so that Flask-Migrate can auto-detect them.

from app.models.user import User                                     # noqa
from app.models.product import Product                               # noqa
from app.models.vendor import Vendor, VendorProduct                  # noqa
from app.models.sku import SKU                                       # noqa
from app.models.vendor_order import VendorOrder, VendorOrderDetail   # noqa
from app.models.vendor_invoice import (                              # noqa
    VendorInvoice,
    VendorInvoiceDetail,
)
from app.models.vendor_return import VendorReturn, VendorReturnDetail  # noqa
from app.models.customer import Customer                             # noqa
from app.models.customer_order import CustomerOrder                  # noqa
from app.models.customer_order_detail import CustomerOrderDetail    # noqa
from app.models.customer_invoice import (                            # noqa
    CustomerInvoice,
    CustomerInvDetail,
)
from app.models.payment import Payment                               # noqa
from app.models.dispatch import Dispatch                             # noqa
from app.models.customer_return import (                             # noqa
    CustomerReturn,
    CustomerReturnDetail,
)
from app.models.packing_slip import PackingSlip, PackingSlipDetail      # noqa
from app.models.stock_adjustment import StockAdjustment              # noqa
from app.models.delivery_receipt import (                             # noqa
    DeliveryReceipt,
    DeliveryReceiptDetail,
)
