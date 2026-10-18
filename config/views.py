from django.db.models import Avg, Sum
from django.views.generic import TemplateView

from accounts.permissions import RolePermissionMixin
from products.choices import (
    AuctionHouseChoices,
    AuctionStatusChoices,
    ProductSourceTypeChoices,
    ProductStatusChoices,
)
from products.models import Auction, Product
from products.services import is_expert_restricted_user


def home(request):
    from django.shortcuts import redirect
    return redirect('accounts:login')


class StatisticsView(RolePermissionMixin, TemplateView):
    template_name = 'dashboard/statistics.html'
    permission_required = 'products.add_product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Product statistics
        all_products = Product.objects.all()
        if is_expert_restricted_user(user):
            # Expert-restricted users only see their assigned products
            all_products = all_products.filter(assigned_expert=user)
        
        # General product stats
        context['product_stats'] = {
            'total_products': all_products.count(),
            'manual_products': all_products.filter(source_type=ProductSourceTypeChoices.MANUAL).count(),
            'auction_products': all_products.filter(source_type__in=[
                ProductSourceTypeChoices.CHRISTIES,
                ProductSourceTypeChoices.SOTHEBYS,
                ProductSourceTypeChoices.OTHER_AUCTION,
            ]).count(),
            'to_buy_products': all_products.filter(to_buy=True).count(),
            'cancelled_products': all_products.filter(is_cancelled=True).count(),
            'notable_products': all_products.filter(is_notable=True).count(),
            'expert_review_products': all_products.filter(needs_expert_review=True).count(),
            'final_inspection_done': all_products.filter(final_inspection_done=True).count(),
            'has_initial_info': all_products.filter(has_initial_info=True).count(),
            'has_all_prices': all_products.filter(has_all_prices=True).count(),
        }
        
        # Products by status
        status_counts = {}
        for status_value, status_label in ProductStatusChoices.choices:
            status_counts[status_label] = all_products.filter(status=status_value).count()
        context['product_stats']['by_status'] = status_counts
        
        # Products by source type
        source_counts = {}
        for source_value, source_label in ProductSourceTypeChoices.choices:
            source_counts[source_label] = all_products.filter(source_type=source_value).count()
        context['product_stats']['by_source'] = source_counts
        
        # Price statistics
        price_stats = all_products.aggregate(
            total_suggested_price=Sum('suggested_price'),
            total_suitable_price=Sum('suitable_price'),
            avg_suggested_price=Avg('suggested_price'),
            avg_suitable_price=Avg('suitable_price'),
        )
        context['product_stats']['price'] = price_stats
        
        # Auction statistics
        all_auctions = Auction.objects.all()
        
        context['auction_stats'] = {
            'total_auctions': all_auctions.count(),
            'upcoming_auctions': all_auctions.filter(status=AuctionStatusChoices.UPCOMING).count(),
            'ongoing_auctions': all_auctions.filter(status=AuctionStatusChoices.ONGOING).count(),
            'ended_auctions': all_auctions.filter(status=AuctionStatusChoices.ENDED).count(),
            'total_lots': all_auctions.aggregate(total=Sum('total_lots'))['total'] or 0,
            'entered_lots': all_auctions.aggregate(total=Sum('entered_lots_count'))['total'] or 0,
            'to_buy_count': all_auctions.aggregate(total=Sum('to_buy_count'))['total'] or 0,
            'cancelled_lots': all_auctions.aggregate(total=Sum('cancelled_lots_count'))['total'] or 0,
            'expert_lots': all_auctions.aggregate(total=Sum('expert_lots_count'))['total'] or 0,
            'notable_lots': all_auctions.aggregate(total=Sum('notable_lots_count'))['total'] or 0,
            'final_inspection_count': all_auctions.aggregate(total=Sum('final_inspection_count'))['total'] or 0,
        }
        
        # Auctions by house
        house_counts = {}
        for house_value, house_label in AuctionHouseChoices.choices:
            house_counts[house_label] = all_auctions.filter(source_house=house_value).count()
        context['auction_stats']['by_house'] = house_counts
        
        # Auctions by status
        auction_status_counts = {}
        for status_value, status_label in AuctionStatusChoices.choices:
            auction_status_counts[status_label] = all_auctions.filter(status=status_value).count()
        context['auction_stats']['by_status'] = auction_status_counts
        
        context['page_title'] = 'آمار و گزارشات'
        return context
