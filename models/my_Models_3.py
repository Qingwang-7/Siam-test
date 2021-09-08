# Kaiyu Li
# https://github.com/likyoo
#

import torch.nn as nn
import torch

class conv_block_nested(nn.Module):
    def __init__(self, in_ch, mid_ch, out_ch):
        super(conv_block_nested, self).__init__()
        self.activation = nn.ReLU(inplace=True)
        self.conv1 = nn.Conv2d(in_ch, mid_ch, kernel_size=3, padding=1, bias=True)
        self.bn1 = nn.BatchNorm2d(mid_ch) # 在卷积神经网络的卷积层之后总会添加BatchNorm2d进行数据的归一化处理，这使得数据在进行Relu之前不会因为数据过大而导致网络性能的不稳定
        self.conv2 = nn.Conv2d(mid_ch, out_ch, kernel_size=3, padding=1, bias=True)
        self.bn2 = nn.BatchNorm2d(out_ch)

    def forward(self, x):
        x = self.conv1(x)
        identity = x
        x = self.bn1(x)
        x = self.activation(x)

        x = self.conv2(x)
        x = self.bn2(x)
        output = self.activation(x + identity)
        return output


class up(nn.Module):
    def __init__(self, in_ch, bilinear=False):
        super(up, self).__init__()

        if bilinear:
            self.up = nn.Upsample(scale_factor=2,
                                  mode='bilinear',
                                  align_corners=True)
        else:
            self.up = nn.ConvTranspose2d(in_ch, in_ch, 2, stride=2)

    def forward(self, x):

        x = self.up(x)
        return x


class ChannelAttention(nn.Module):
    def __init__(self, in_channels, ratio = 16):
        super(ChannelAttention, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc1 = nn.Conv2d(in_channels,in_channels//ratio,1,bias=False)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Conv2d(in_channels//ratio, in_channels,1,bias=False)
        self.sigmod = nn.Sigmoid()
    def forward(self,x):
        avg_out = self.fc2(self.relu1(self.fc1(self.avg_pool(x))))
        max_out = self.fc2(self.relu1(self.fc1(self.max_pool(x))))
        out = avg_out + max_out
        return self.sigmod(out)



class SNUNet_ECAM(nn.Module):
    # SNUNet-CD with ECAM
    def __init__(self, in_ch=3, out_ch=2):
        super(SNUNet_ECAM, self).__init__()
        torch.nn.Module.dump_patches = True
        n1 = 24     # the initial number of channels of feature map  特征图的初始通道数
        filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16,16]

        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)

        self.conv0_0 = conv_block_nested(in_ch, filters[0], filters[0])
        self.conv1_0 = conv_block_nested(filters[0], filters[1], filters[1])
        self.Up1_0 = up(filters[1])
        self.conv2_0 = conv_block_nested(filters[1], filters[2], filters[2])
        self.Up2_0 = up(filters[2])
        self.conv3_0 = conv_block_nested(filters[2], filters[3], filters[3])
        self.Up3_0 = up(filters[3])
        # self.conv4_0 = conv_block_nested(filters[3], filters[4], filters[4])
        # self.Up4_0 = up(filters[4])

        self.conv0_1_B = conv_block_nested(filters[0] * 2 + filters[1], filters[0], 16)
        self.conv1_1_B = conv_block_nested(filters[1] * 2 + filters[2], filters[1], filters[1])
        self.Up1_1_B = up(filters[1])
        self.conv2_1_B = conv_block_nested(filters[2] * 2 + filters[3], filters[2], filters[2])
        self.Up2_1_B = up(filters[2])
        # self.conv3_1 = conv_block_nested(filters[3] * 2 + filters[4], filters[3], filters[3])
        # self.Up3_1 = up(filters[3])

        self.conv0_2_B = conv_block_nested(filters[0] * 3 + filters[1], filters[0], 16)
        self.conv1_2_B = conv_block_nested(filters[1] * 3 + filters[2], filters[1], filters[1])
        self.Up1_2_B = up(filters[1])
        # self.conv2_2 = conv_block_nested(filters[2] * 3 + filters[3], filters[2], filters[2])
        # self.Up2_2 = up(filters[2])

        self.conv0_3_B = conv_block_nested(filters[0] * 4 + filters[1], filters[0], 16)
        # self.conv1_3 = conv_block_nested(filters[1] * 4 + filters[2], filters[1], filters[1])
        # self.Up1_3 = up(filters[1])
        #  A------------------------------------------------------------------------------------
        self.conv0_1_A = conv_block_nested(filters[0] * 2 + filters[1], filters[0], 16)
        self.conv1_1_ = conv_block_nested(filters[1] * 2 + filters[2], filters[1], filters[1])
        self.Up1_1_A = up(filters[1])
        self.conv2_1_A = conv_block_nested(filters[2] * 2 + filters[3], filters[2], filters[2])
        self.Up2_1_A = up(filters[2])
        # self.conv3_1 = conv_block_nested(filters[3] * 2 + filters[4], filters[3], filters[3])
        # self.Up3_1 = up(filters[3])

        self.conv0_2_A = conv_block_nested(filters[0] * 3 + filters[1], filters[0], 16)
        self.conv1_2_A = conv_block_nested(filters[1] * 3 + filters[2], filters[1], filters[1])
        self.Up1_2_A = up(filters[1])
        # self.conv2_2 = conv_block_nested(filters[2] * 3 + filters[3], filters[2], filters[2])
        # self.Up2_2 = up(filters[2])

        self.conv0_3_A = conv_block_nested(filters[0] * 4 + filters[1], filters[0], 16)
        # self.conv1_3 = conv_block_nested(filters[1] * 4 + filters[2], filters[1], filters[1])
        # self.Up1_3 = up(filters[1])

        # self.conv0_4 = conv_block_nested(filters[0] * 5 + filters[1], filters[0], filters[0])
        #  A-----------------------------------------------------------------------------------
        self.ca = ChannelAttention(filters[0] * 4, ratio=16)
        self.ca1 = ChannelAttention(filters[0], ratio=16 // 4)

        self.conv_final = nn.Conv2d(filters[0] * 4, out_ch, kernel_size=1)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, (nn.BatchNorm2d, nn.GroupNorm)):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)


    def forward(self, xA, xB):
        '''xA'''
        x0_0A = self.conv0_0(xA)
        x1_0A = self.conv1_0(self.pool(x0_0A))
        x2_0A = self.conv2_0(self.pool(x1_0A))
        x3_0A = self.conv3_0(self.pool(x2_0A))
        # x4_0A = self.conv4_0(self.pool(x3_0A))
        '''xB'''
        x0_0B = self.conv0_0(xB)
        x1_0B = self.conv1_0(self.pool(x0_0B))
        x2_0B = self.conv2_0(self.pool(x1_0B))
        x3_0B = self.conv3_0(self.pool(x2_0B))
        # x4_0B = self.conv4_0(self.pool(x3_0B))

        x0_1_B = self.conv0_1_B(torch.cat([x0_0A, x0_0B, self.Up1_0(x1_0B)], 1))  # 1
        x1_1_B = self.conv1_1_B(torch.cat([x1_0A, x1_0B, self.Up2_0(x2_0B)], 1))
        x0_2_B = self.conv0_2_B(torch.cat([x0_0A, x0_0B, x0_1_B, self.Up1_1_B(x1_1_B)], 1)) # 2


        x2_1_B = self.conv2_1_B(torch.cat([x2_0A, x2_0B, self.Up3_0(x3_0B)], 1))
        x1_2_B = self.conv1_2_B(torch.cat([x1_0A, x1_0B, x1_1_B, self.Up2_1_B(x2_1_B)], 1))
        x0_3_B = self.conv0_3_B(torch.cat([x0_0A, x0_0B, x0_1_B, x0_2_B, self.Up1_2_B(x1_2_B)], 1)) # 3
        # A---------------------------------------------------------------------------------------------
        x0_1_A = self.conv0_1_A(torch.cat([x0_0B, x0_0A, self.Up1_0(x1_0A)], 1))  # 1
        x1_1_A = self.conv1_1_A(torch.cat([x1_0B, x1_0A, self.Up2_0(x2_0A)], 1))
        x0_2_A = self.conv0_2_A(torch.cat([x0_0B, x0_0A, x0_1_A, self.Up1_1_A(x1_1_A)], 1))  # 2

        x2_1_A = self.conv2_1_A(torch.cat([x2_0B, x2_0A, self.Up3_0(x3_0A)], 1))
        x1_2_A = self.conv1_2_A(torch.cat([x1_0B, x1_0A, x1_1_A, self.Up2_1_A(x2_1_A)], 1))
        x0_3_A = self.conv0_3_A(torch.cat([x0_0B, x0_0A, x0_1_A, x0_2_A, self.Up1_2_A(x1_2_A)], 1))  # 3

        # x3_1 = self.conv3_1(torch.cat([x3_0A, x3_0B, self.Up4_0(x4_0B)], 1))
        # x2_2 = self.conv2_2(torch.cat([x2_0A, x2_0B, x2_1_B, self.Up3_1(x3_1)], 1))
        # x1_3 = self.conv1_3(torch.cat([x1_0A, x1_0B, x1_1_B, x1_2_B, self.Up2_2(x2_2)], 1))
        # x0_4 = self.conv0_4(torch.cat([x0_0A, x0_0B, x0_1_B, x0_2_B, x0_3_B, self.Up1_3(x1_3)], 1)) # 4

        out = torch.cat([x0_1_B,x0_1_A, x0_2_B, x0_2_A,x0_3_B, x0_3_A], 1)

        intra = torch.sum(torch.stack((x0_1_B,x0_1_A, x0_2_B, x0_2_A,x0_3_B, x0_3_A)), dim=0)
        ca1 = self.ca1(intra)
        out = self.ca(out) * (out + ca1.repeat(1, 4, 1, 1))  # ？？？
        out = self.conv_final(out)

        return (out, )


# class Siam_NestedUNet_Conc(nn.Module):
#     # SNUNet-CD without Attention
#     def __init__(self, in_ch=3, out_ch=2):
#         super(Siam_NestedUNet_Conc, self).__init__()
#         torch.nn.Module.dump_patches = True
#         n1 = 32     # the initial number of channels of feature map
#         filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16]
#
#         self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
#
#         self.conv0_0 = conv_block_nested(in_ch, filters[0], filters[0])
#         self.conv1_0 = conv_block_nested(filters[0], filters[1], filters[1])
#         self.Up1_0 = up(filters[1])
#         self.conv2_0 = conv_block_nested(filters[1], filters[2], filters[2])
#         self.Up2_0 = up(filters[2])
#         self.conv3_0 = conv_block_nested(filters[2], filters[3], filters[3])
#         self.Up3_0 = up(filters[3])
#         self.conv4_0 = conv_block_nested(filters[3], filters[4], filters[4])
#         self.Up4_0 = up(filters[4])
#
#         self.conv0_1_B = conv_block_nested(filters[0] * 2 + filters[1], filters[0], filters[0])
#         self.conv1_1_B = conv_block_nested(filters[1] * 2 + filters[2], filters[1], filters[1])
#         self.Up1_1_B = up(filters[1])
#         self.conv2_1_B = conv_block_nested(filters[2] * 2 + filters[3], filters[2], filters[2])
#         self.Up2_1_B = up(filters[2])
#         self.conv3_1 = conv_block_nested(filters[3] * 2 + filters[4], filters[3], filters[3])
#         self.Up3_1 = up(filters[3])
#
#         self.conv0_2_B = conv_block_nested(filters[0] * 3 + filters[1], filters[0], filters[0])
#         self.conv1_2_B = conv_block_nested(filters[1] * 3 + filters[2], filters[1], filters[1])
#         self.Up1_2_B = up(filters[1])
#         self.conv2_2 = conv_block_nested(filters[2] * 3 + filters[3], filters[2], filters[2])
#         self.Up2_2 = up(filters[2])
#
#         self.conv0_3_B = conv_block_nested(filters[0] * 4 + filters[1], filters[0], filters[0])
#         self.conv1_3 = conv_block_nested(filters[1] * 4 + filters[2], filters[1], filters[1])
#         self.Up1_3 = up(filters[1])
#
#         self.conv0_4 = conv_block_nested(filters[0] * 5 + filters[1], filters[0], filters[0])
#
#         self.final1 = nn.Conv2d(filters[0], out_ch, kernel_size=1)
#         self.final2 = nn.Conv2d(filters[0], out_ch, kernel_size=1)
#         self.final3 = nn.Conv2d(filters[0], out_ch, kernel_size=1)
#         self.final4 = nn.Conv2d(filters[0], out_ch, kernel_size=1)
#         self.conv_final = nn.Conv2d(out_ch * 4, out_ch, kernel_size=1)
#
#         for m in self.modules():
#             if isinstance(m, nn.Conv2d):
#                 nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
#             elif isinstance(m, (nn.BatchNorm2d, nn.GroupNorm)):
#                 nn.init.constant_(m.weight, 1)
#                 nn.init.constant_(m.bias, 0)
#
#
#     def forward(self, xA, xB):
#         '''xA'''
#         x0_0A = self.conv0_0(xA)
#         x1_0A = self.conv1_0(self.pool(x0_0A))
#         x2_0A = self.conv2_0(self.pool(x1_0A))
#         x3_0A = self.conv3_0(self.pool(x2_0A))
#         # x4_0A = self.conv4_0(self.pool(x3_0A))
#         '''xB'''
#         x0_0B = self.conv0_0(xB)
#         x1_0B = self.conv1_0(self.pool(x0_0B))
#         x2_0B = self.conv2_0(self.pool(x1_0B))
#         x3_0B = self.conv3_0(self.pool(x2_0B))
#         x4_0B = self.conv4_0(self.pool(x3_0B))
#
#         x0_1_B = self.conv0_1_B(torch.cat([x0_0A, x0_0B, self.Up1_0(x1_0B)], 1)) # torch.cat是将两个张量（tensor）拼接在一起  维数1（行）拼接
#         x1_1_B = self.conv1_1_B(torch.cat([x1_0A, x1_0B, self.Up2_0(x2_0B)], 1))
#         x0_2_B = self.conv0_2_B(torch.cat([x0_0A, x0_0B, x0_1_B, self.Up1_1_B(x1_1_B)], 1))
#
#
#         x2_1_B = self.conv2_1_B(torch.cat([x2_0A, x2_0B, self.Up3_0(x3_0B)], 1))
#         x1_2_B = self.conv1_2_B(torch.cat([x1_0A, x1_0B, x1_1_B, self.Up2_1_B(x2_1_B)], 1))
#         x0_3_B = self.conv0_3_B(torch.cat([x0_0A, x0_0B, x0_1_B, x0_2_B, self.Up1_2_B(x1_2_B)], 1))
#
#         x3_1 = self.conv3_1(torch.cat([x3_0A, x3_0B, self.Up4_0(x4_0B)], 1))
#         x2_2 = self.conv2_2(torch.cat([x2_0A, x2_0B, x2_1_B, self.Up3_1(x3_1)], 1))
#         x1_3 = self.conv1_3(torch.cat([x1_0A, x1_0B, x1_1_B, x1_2_B, self.Up2_2(x2_2)], 1))
#         x0_4 = self.conv0_4(torch.cat([x0_0A, x0_0B, x0_1_B, x0_2_B, x0_3_B, self.Up1_3(x1_3)], 1))
#
#
#         output1 = self.final1(x0_1_B)
#         output2 = self.final2(x0_2_B)
#         output3 = self.final3(x0_3_B)
#         output4 = self.final4(x0_4)
#         output = self.conv_final(torch.cat([output1, output2, output3, output4], 1))
#         return (output1, output2, output3, output4, output)
