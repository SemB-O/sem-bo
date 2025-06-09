// components/PlanCard.tsx
import { View, Text, Pressable } from 'react-native';

type PlanCardProps = {
  title: string;
  description: string;
  price: string;
  onPress?: () => void;
};

export default function PlanCard({ title, description, price, onPress }: PlanCardProps) {
  return (
    <View className="w-[340px] h-[280px] p-6 bg-white rounded-2xl shadow-md m-2 flex justify-between">
      <View>
        <Text className="text-2xl font-bold text-gray-900 mb-1">{title}</Text>
        <Text className="text-xs text-gray-500 mb-6">{description}</Text>

        <View className="flex-row items-end space-x-1">
          <Text className="text-base text-gray-900">R$</Text>
          <Text className="text-5xl font-extrabold text-gray-900">{price}</Text>
          <Text className="text-xl font-bold text-gray-900">/mês</Text>
        </View>
      </View>

      <Pressable
        className="bg-black py-2.5 w-full rounded-lg"
        onPress={onPress}
      >
        <Text className="text-white text-center font-medium text-sm">Selecionar</Text>
      </Pressable>
    </View>
  );
}
